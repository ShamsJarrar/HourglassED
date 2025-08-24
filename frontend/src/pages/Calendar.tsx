import NavBar from '../components/NavBar'
import FullCalendar from '@fullcalendar/react'
import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import listPlugin from '@fullcalendar/list'
import rrulePlugin from '@fullcalendar/rrule'
import multiMonthPlugin from '@fullcalendar/multimonth'
import { getEvents } from '../lib/events'
import type { EventContentArg } from '@fullcalendar/core'
import type { EventResponse } from '../types/api'
import EventModal from '../components/EventModal'
import CreateEventModal from '../components/CreateEventModal'
import FiltersModal from '../components/FiltersModal'
import { parseJwt } from '../utils/jwt'
import { useToast } from '../components/Toast'
// CSS loaded via CDN in index.html to avoid import-analysis issues

export default function Calendar() {
  const calendarRef = useRef<FullCalendar | null>(null)
  const [open, setOpen] = useState(false)
  const [toolbarRightEl, setToolbarRightEl] = useState<HTMLElement | null>(null)
  const [currentViewLabel, setCurrentViewLabel] = useState('Month')
  const [events, setEvents] = useState<{
    id: string
    title: string
    start: string
    end: string
    backgroundColor?: string
    borderColor?: string
    textColor?: string
  }[]>([])
  // reserved for future loading indicators
  // const [isLoading, setIsLoading] = useState(false)
  const [selected, setSelected] = useState<EventResponse | null>(null)
  const [isOwner, setIsOwner] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [filters, setFilters] = useState<{ owned_only?: boolean; event_types?: number[] | null }>({})
  const { show } = useToast()

  const viewOptions: { id: string; label: string }[] = [
    { id: 'multiMonthYear', label: 'Year' },
    { id: 'dayGridMonth', label: 'Month' },
    { id: 'timeGridWeek', label: 'Week' },
    { id: 'timeGridDay', label: 'Day' },
    { id: 'listWeek', label: 'List' },
  ]

  const changeView = (id: string, label: string) => {
    const api = calendarRef.current?.getApi()
    api?.changeView(id)
    setCurrentViewLabel(label)
    setOpen(false)
  }

  useEffect(() => {
    // Find FullCalendar right toolbar chunk to align custom button with title and controls
    const el = document.querySelector('.fc .fc-toolbar .fc-toolbar-chunk:last-child') as HTMLElement | null
    if (el) setToolbarRightEl(el)
  }, [])

  // Refetch events whenever filters change
  useEffect(() => {
    const api = calendarRef.current?.getApi()
    if (api) {
      const view = api.view
      // Trigger fetch with the current visible range and latest filters
      handleDatesSet({ start: view.activeStart, end: view.activeEnd })
    }
  }, [filters])

  // Fetch events when the calendar date range changes
  const handleDatesSet = async (arg: { start: Date; end: Date }) => {
    try {
      const startIso = arg.start.toISOString()
      const endIso = arg.end.toISOString()
      const data: EventResponse[] = await getEvents({
        start_time: startIso,
        end_time: endIso,
        ...(filters.owned_only ? { owned_only: true } : {}),
        ...(filters.event_types && filters.event_types.length ? { event_types: filters.event_types } : {}),
      })
      const mapped = data.map((e) => {
        const normalizeHex = (val?: string) => {
          if (!val) return undefined
          const v = val.startsWith('#') ? val : `#${val}`
          return v.length === 4 || v.length === 7 ? v : undefined
        }
        const darkenHex = (hex?: string, amount = 35) => {
          if (!hex) return undefined
          let c = hex.replace('#', '')
          if (c.length === 3) c = c.split('').map((x) => x + x).join('')
          const r = Math.max(0, parseInt(c.substring(0, 2), 16) - amount)
          const g = Math.max(0, parseInt(c.substring(2, 4), 16) - amount)
          const b = Math.max(0, parseInt(c.substring(4, 6), 16) - amount)
          const toHex = (n: number) => n.toString(16).padStart(2, '0')
          return `#${toHex(r)}${toHex(g)}${toHex(b)}`
        }
        const bg = normalizeHex(e.color || undefined)
        const border = darkenHex(bg)
        return {
        id: String(e.event_id),
        title: e.title,
        start: e.start_time,
        end: e.end_time,
        backgroundColor: bg,
        borderColor: border || bg,
        extendedProps: {
          header: e.header ?? undefined,
          event_type: e.event_type,
          user_id: e.user_id,
          notes: e.notes ?? undefined,
          raw_start_time: e.start_time,
          raw_end_time: e.end_time,
        },
        }
      })
      setEvents(mapped)
    } catch (err) {
      // TODO: surface error toast/UI later
      console.error('Failed to load events', err)
    }
  }

  const getContrastTextColor = (hex?: string) => {
    if (!hex) return '#633D00'
    let c = hex.replace('#', '')
    if (c.length === 3) c = c.split('').map((x) => x + x).join('')
    const r = parseInt(c.substring(0, 2), 16)
    const g = parseInt(c.substring(2, 4), 16)
    const b = parseInt(c.substring(4, 6), 16)
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return luminance < 140 ? '#FAF0DC' : '#533300'
  }

  const renderEventContent = (arg: EventContentArg) => {
    const header = (arg.event.extendedProps as { header?: string | undefined })?.header
    const label = header ? `${header.toUpperCase()}: ${arg.event.title}` : arg.event.title
    const bg = (arg.backgroundColor as string) || undefined
    const color = getContrastTextColor(bg)
    return <div className="truncate" style={{ color }}>{label}</div>
  }

  return (
    <div className="min-h-screen bg-[#FAF0DC]">
      <NavBar />
      <main className="mx-auto w-full px-6 py-6">
        <div className="flex items-stretch gap-6">
          {/* Left panel (smaller section) */}
          <aside className="w-45 shrink-0 rounded-xl bg-[#FAF0DC] text-[#FAF0DC] p-3 flex flex-col justify-center space-y-20">
            <button onClick={() => setCreateOpen(true)} className="w-full inline-flex items-center justify-center gap-3 rounded-xl text-lg bg-[#633D00] text-[#FAF0DC] font-medium px-4 py-4 transition-colors hover:bg-[#765827] shadow-xl">
              <img src="/icons/plus_icon.svg" alt="Create" className="h-5 w-5" />
              <span>Create</span>
            </button>
            <button onClick={() => setFiltersOpen(true)} className="w-10/12 self-center inline-flex items-center justify-center gap-3 rounded-xl bg-[#FAF0DC] text-[#633D00] font-medium px-4 py-3 transition-colors hover:bg-[#ead9be] border-1 border-[#633D00]">
              <img src="/icons/filter_icon.svg" alt="Filters" className="h-4 w-4" />
              <span>Filters</span>
            </button>
            <button className="w-10/12 self-center inline-flex items-center justify-center gap-3 rounded-xl bg-[#FAF0DC] text-[#633D00] font-medium px-4 py-3 transition-colors hover:bg-[#ead9be] border-1 border-[#633D00]">
              <span>Organize with agent</span>
            </button>
          </aside>

          {/* Right panel (bigger section): Calendar */}
          <section className="flex-1 min-w-0 rounded-xl bg-[#FFF8EB] p-3">
            <FullCalendar
              ref={calendarRef}
              plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin, listPlugin, rrulePlugin, multiMonthPlugin]}
              initialView="dayGridMonth"
              headerToolbar={{ left: 'prev,next today', center: 'title', right: '' }}
              height="auto"
              editable={false}
              selectable={true}
              dayMaxEvents={true}
              eventDisplay="block"
              events={events}
              datesSet={handleDatesSet}
              eventContent={renderEventContent}
              eventClick={(info) => {
                const e = info.event
                const ep: any = e.extendedProps || {}
                const mapped: EventResponse = {
                  event_id: Number(e.id),
                  user_id: typeof ep.user_id === 'number' ? ep.user_id : 0,
                  event_type: typeof ep.event_type === 'number' ? ep.event_type : 0,
                  header: ep.header,
                  title: e.title,
                  start_time: typeof ep.raw_start_time === 'string' ? ep.raw_start_time : e.startStr,
                  end_time: typeof ep.raw_end_time === 'string' ? ep.raw_end_time : e.endStr,
                  color: e.backgroundColor || undefined,
                  notes: ep.notes,
                  linked_event_id: undefined,
                  recurring_event_id: undefined,
                }
                setSelected(mapped)
                const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
                const userIdFromToken = token ? Number((parseJwt(token)?.sub as any) ?? 0) : 0
                setIsOwner(mapped.user_id === userIdFromToken)
              }}
            />
            {toolbarRightEl && createPortal(
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setOpen((v) => !v)}
                  className="inline-flex items-center rounded-md border-2 border-[#633D00] bg-[#FFF8EB] px-3 py-1.5 text-[#633D00] font-medium transition-colors hover:bg-[#ead9be]"
                >
                  {currentViewLabel}
                  <img src="/icons/down_icon.svg" alt="Open" className="ml-2 h-4 w-4" />
                </button>
                {open && (
                  <div className="absolute right-0 z-10 mt-2 w-40 overflow-hidden rounded-md border border-[#633D00]/40 bg-[#633D00] text-[#FAF0DC] shadow-lg">
                    {viewOptions.map((opt) => (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => changeView(opt.id, opt.label)}
                        className="block w-full px-3 py-2 text-left hover:bg-[#8a5a1d]"
                      >
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>,
              toolbarRightEl
            )}
          </section>
        </div>
      </main>
      <EventModal
        event={selected}
        isOwner={isOwner}
        open={!!selected}
        onClose={() => {
          setSelected(null)
          // After save, refetch events for current visible range
          const api = calendarRef.current?.getApi()
          if (api) {
            const view = api.view
            // trigger datesSet manually
            handleDatesSet({ start: view.activeStart, end: view.activeEnd })
          }
        }}
      />
      <CreateEventModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          const api = calendarRef.current?.getApi()
          if (api) {
            const view = api.view
            handleDatesSet({ start: view.activeStart, end: view.activeEnd })
          }
        }}
      />
      <FiltersModal
        open={filtersOpen}
        onClose={() => setFiltersOpen(false)}
        value={filters}
        onChange={(next) => {
          setFilters(next)
          const api = calendarRef.current?.getApi()
          if (api) {
            const view = api.view
            handleDatesSet({ start: view.activeStart, end: view.activeEnd })
          }
        }}
      />
    </div>
  )
}



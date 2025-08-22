import { useEffect, useMemo, useState } from 'react'
import type { EventResponse } from '../types/api'
import { getEventClasses, updateEvent, type EventClassResponse } from '../lib/events'
import type { EventUpdate } from '../types/api'

interface Props {
  event: EventResponse | null
  isOwner: boolean
  open: boolean
  onClose: () => void
  onSaved?: () => void
}

export default function EventModal({ event, isOwner, open, onClose }: Props) {
  const [classes, setClasses] = useState<EventClassResponse[]>([])
  const [title, setTitle] = useState('')
  const [header, setHeader] = useState<string | undefined>('')
  const [color, setColor] = useState<string | undefined>('')
  const [notes, setNotes] = useState<string | undefined>('')
  const [selectedClassName, setSelectedClassName] = useState<string>('')
  const [useCustomType, setUseCustomType] = useState<boolean>(false)
  const [customTypeName, setCustomTypeName] = useState<string>('')
  const [startLocal, setStartLocal] = useState<string>('')
  const [endLocal, setEndLocal] = useState<string>('')

  useEffect(() => {
    if (!open) return
    getEventClasses().then(setClasses).catch(() => setClasses([]))
  }, [open])

  useEffect(() => {
    if (!event) return
    setTitle(event.title)
    setHeader(event.header ?? undefined)
    setColor(event.color ?? undefined)
    setNotes(event.notes ?? undefined)
  }, [event])

  const classNameById = useMemo(() => {
    const map = new Map<number, string>()
    classes.forEach(c => map.set(c.class_id, c.class_name))
    return map
  }, [classes])

  useEffect(() => {
    if (!event) return
    const name = classNameById.get(event.event_type) ?? ''
    setSelectedClassName(name)
    setUseCustomType(false)
    setCustomTypeName('')
    // initialize editable start/end values
    const toLocalInput = (iso: string) => {
      const d = new Date(iso)
      const pad = (n: number) => String(n).padStart(2, '0')
      const yyyy = d.getFullYear()
      const MM = pad(d.getMonth() + 1)
      const dd = pad(d.getDate())
      const hh = pad(d.getHours())
      const mm = pad(d.getMinutes())
      return `${yyyy}-${MM}-${dd}T${hh}:${mm}`
    }
    setStartLocal(toLocalInput(event.start_time))
    setEndLocal(toLocalInput(event.end_time))
  }, [event, classNameById])

  if (!open || !event) return null

  const readOnly = !isOwner

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30">
      <div className="w-[520px] max-w-[92vw] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[#633D00]">Event Details</h2>
          <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
        </div>

        <div className="space-y-3 text-[#633D00]">
          <div>
            <label className="block text-sm mb-1">Type</label>
            {readOnly ? (
              <div className="rounded-md border border-[#633D00] px-3 py-2 bg-white">
                {classNameById.get(event.event_type) ?? (selectedClassName || '—')}
              </div>
            ) : (
              <>
                <select
                  value={useCustomType ? '__custom__' : selectedClassName}
                  onChange={(e) => {
                    const val = e.target.value
                    if (val === '__custom__') {
                      setUseCustomType(true)
                    } else {
                      setUseCustomType(false)
                      setSelectedClassName(val)
                    }
                  }}
                  className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                >
                  {classes.map((c) => (
                    <option key={c.class_id} value={c.class_name}>{c.class_name}</option>
                  ))}
                  <option value="__custom__">Add custom…</option>
                </select>
                {useCustomType && (
                  <input
                    value={customTypeName}
                    onChange={(e) => setCustomTypeName(e.target.value)}
                    className="mt-2 w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                    placeholder="Enter new type name"
                  />
                )}
              </>
            )}
          </div>

          <div>
            <label className="block text-sm mb-1">Header</label>
            <input value={header ?? ''} onChange={(e) => setHeader(e.target.value)} disabled={readOnly} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
          </div>

          <div>
            <label className="block text-sm mb-1">Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={readOnly} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1">Start</label>
              {readOnly ? (
                <div className="rounded-md border border-[#633D00] px-3 py-2 bg-white">
                  {new Date(event.start_time).toLocaleString()}
                </div>
              ) : (
                <input
                  type="datetime-local"
                  value={startLocal}
                  onChange={(e) => setStartLocal(e.target.value)}
                  className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                />
              )}
            </div>
            <div>
              <label className="block text-sm mb-1">End</label>
              {readOnly ? (
                <div className="rounded-md border border-[#633D00] px-3 py-2 bg-white">
                  {new Date(event.end_time).toLocaleString()}
                </div>
              ) : (
                <input
                  type="datetime-local"
                  value={endLocal}
                  onChange={(e) => setEndLocal(e.target.value)}
                  className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                />
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1">Color</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={(color?.startsWith('#') ? color : `#${color ?? 'ffffff'}`)}
                onChange={(e) => setColor(e.target.value)}
                disabled={readOnly}
                className="h-9 w-9 rounded-md border border-[#633D00] bg-white"
              />
              <input
                value={color ?? ''}
                onChange={(e) => setColor(e.target.value)}
                disabled={readOnly}
                className="flex-1 rounded-md border border-[#633D00] px-3 py-2 bg-white"
                placeholder="#FFD700 or FFD700"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1">Notes</label>
            <textarea value={notes ?? ''} onChange={(e) => setNotes(e.target.value)} disabled={readOnly} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white min-h-24" />
          </div>
        </div>

        <div className="mt-5 flex justify-end gap-3">
          {isOwner && (
            <button
              onClick={async () => {
                if (!event) return
                const typeName = (useCustomType ? customTypeName : selectedClassName).trim()
                const body: EventUpdate = {
                  event_type: typeName || undefined,
                  header: header ?? undefined,
                  title: title,
                  start_time: startLocal ? new Date(startLocal).toISOString() : undefined,
                  end_time: endLocal ? new Date(endLocal).toISOString() : undefined,
                  color: color ?? undefined,
                  notes: notes ?? undefined,
                }
                try {
                  await updateEvent(event.event_id, body)
                  onClose()
                  // optional: expose onSaved to trigger refetch from parent
                } catch (e) {
                  console.error('Failed to update event', e)
                }
              }}
              className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827]"
            >
              Save
            </button>
          )}
        </div>
      </div>
    </div>
  )
}



import { useEffect, useMemo, useState } from 'react'
import type { EventCreate } from '../types/api'
import { getEventClasses, type EventClassResponse, createEvent } from '../lib/events'
import { getFriendsList, type FriendsListResponseItem } from '../lib/friends'
import { createInvitation } from '../lib/invitations'
import { useToast } from './Toast'

interface Props {
  open: boolean
  onClose: () => void
  onCreated?: () => void
}

export default function CreateEventModal({ open, onClose, onCreated }: Props) {
  const { show } = useToast()
  const [classes, setClasses] = useState<EventClassResponse[]>([])
  const [selectedClassName, setSelectedClassName] = useState<string>('')
  const [useCustomType, setUseCustomType] = useState<boolean>(false)
  const [customTypeName, setCustomTypeName] = useState<string>('')
  const [header, setHeader] = useState<string | undefined>('')
  const [title, setTitle] = useState<string>('')
  const [startLocal, setStartLocal] = useState<string>('')
  const [endLocal, setEndLocal] = useState<string>('')
  const [color, setColor] = useState<string | undefined>('')
  const [notes, setNotes] = useState<string | undefined>('')
  const [submitting, setSubmitting] = useState(false)
  const [friends, setFriends] = useState<FriendsListResponseItem[] | null>(null)
  const [selectedFriendId, setSelectedFriendId] = useState<number | ''>('')
  const [inviteQueue, setInviteQueue] = useState<FriendsListResponseItem[]>([])
  const availableFriends = useMemo(
    () => (friends ?? []).filter((f) => !inviteQueue.some((q) => q.friend_id === f.friend_id)),
    [friends, inviteQueue]
  )

  useEffect(() => {
    if (!open) return
    getEventClasses()
      .then((list) => {
        setClasses(list)
        if (list.length > 0) {
          setSelectedClassName(list[0].class_name)
        }
      })
      .catch(() => setClasses([]))
  }, [open])

  // Load friends list for invitations
  useEffect(() => {
    if (!open) return
    let cancelled = false
    getFriendsList()
      .then((list) => {
        if (!cancelled) setFriends(list)
      })
      .catch(() => {
        if (!cancelled) setFriends([])
      })
    return () => { cancelled = true }
  }, [open])

  useEffect(() => {
    if (!open) return
    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const toLocalInput = (d: Date) => {
      const yyyy = d.getFullYear()
      const MM = pad(d.getMonth() + 1)
      const dd = pad(d.getDate())
      const hh = pad(d.getHours())
      const mm = pad(d.getMinutes())
      return `${yyyy}-${MM}-${dd}T${hh}:${mm}`
    }
    const end = new Date(now.getTime() + 60 * 60 * 1000)
    setStartLocal(toLocalInput(now))
    setEndLocal(toLocalInput(end))
    setHeader('')
    setTitle('')
    setColor('')
    setNotes('')
    setUseCustomType(false)
    setCustomTypeName('')
  }, [open])

  const classNames = useMemo(() => classes.map((c) => c.class_name), [classes])

  if (!open) return null

  const basicColors = [
    '#FFD700', '#FF8C00', '#FF4D4D', '#00C853',
    '#1E90FF', '#8A2BE2', '#FF69B4', '#00CED1',
    '#795548', '#9E9E9E', '#000000', '#FFFFFF',
  ]

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={onClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Create Event</h2>
            <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          <div className="space-y-3 text-[#633D00] flex-1 overflow-y-auto no-scrollbar">
            <div>
              <label className="block text-sm mb-1">Type *</label>
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
                  {classNames.map((name) => (
                    <option key={name} value={name}>{name}</option>
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
            </div>

            <div>
              <label className="text-sm mb-1 flex items-center">
                <span>Header</span>
                <img
                  src="/icons/info_icon.svg"
                  alt="info"
                  title="Capitalized part of the title (max. 15 chars)"
                  className="ml-1 h-4 w-4 opacity-80"
                />
              </label>
              <input maxLength={15} value={header ?? ''} onChange={(e) => setHeader(e.target.value)} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
            </div>

            <div>
              <label className="block text-sm mb-1">Title *</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm mb-1">Start *</label>
                <input
                  type="datetime-local"
                  value={startLocal}
                  onChange={(e) => setStartLocal(e.target.value)}
                  className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                />
              </div>
              <div>
                <label className="block text-sm mb-1">End *</label>
                <input
                  type="datetime-local"
                  value={endLocal}
                  onChange={(e) => setEndLocal(e.target.value)}
                  className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm mb-1">Color</label>
              <div className="grid grid-cols-8 gap-2 mb-2">
                {basicColors.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setColor(c)}
                    className={`h-6 w-6 rounded-sm border ${(((color ?? '').startsWith('#') ? (color ?? '') : `#${color ?? ''}`).toUpperCase() === c.toUpperCase()) ? 'ring-2 ring-[#633D00]' : 'border-[#633D00]/40'}`}
                    style={{ backgroundColor: c }}
                    aria-label={`Choose color ${c}`}
                    title={c}
                  />
                ))}
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="color"
                  value={(color?.startsWith('#') ? color : `#${color ?? 'ffffff'}`)}
                  onChange={(e) => setColor(e.target.value)}
                  className="h-9 w-9 rounded-md border border-[#633D00] bg-white"
                  title="Custom color"
                  aria-label="Custom color"
                />
                <span className="text-xs text-[#633D00]/70">Custom</span>
              </div>
            </div>

            <div>
              <label className="block text-sm mb-1">Recurrence</label>
              <input disabled value="Not implemented yet" className="w-full rounded-md border border-[#633D00]/40 bg-[#f5efe2] px-3 py-2 text-[#633D00]/70" />
            </div>

            <div>
              <label className="block text-sm mb-1">Notes</label>
              <textarea value={notes ?? ''} onChange={(e) => setNotes(e.target.value)} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white min-h-24" />
            </div>

            <div className="pt-3 border-t border-[#633D00]/30">
              <label className="block text-sm font-medium mb-2">Invitations</label>
              <div className="text-xs text-[#633D00]/70 mb-2">Invitations will be sent after the event is created.</div>
              {inviteQueue.length > 0 && (
                <ul className="mb-2 space-y-2">
                  {inviteQueue.map((f) => (
                    <li key={f.friend_id} className="flex items-center justify-between gap-3 rounded-md border border-[#633D00]/30 bg-white px-3 py-2">
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{f.friend_name}</div>
                        <div className="text-xs text-[#633D00]/70 truncate">{f.friend_email}</div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setInviteQueue((prev) => prev.filter((x) => x.friend_id !== f.friend_id))}
                        className="rounded-md border border-red-700 text-red-700 px-2 py-1 hover:bg-red-50 text-xs"
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              <div className="flex items-center gap-2">
                <select
                  value={selectedFriendId === '' ? '' : String(selectedFriendId)}
                  onChange={(e) => setSelectedFriendId(e.target.value ? Number(e.target.value) : '')}
                  className="flex-1 rounded-md border border-[#633D00] px-3 py-2 bg-white"
                >
                  <option value="">Select a friend…</option>
                  {availableFriends.map((f) => (
                    <option key={f.friend_id} value={f.friend_id}>{`${f.friend_name} — ${f.friend_email}`}</option>
                  ))}
                </select>
                <button
                  type="button"
                  disabled={selectedFriendId === '' || inviteQueue.some((q) => q.friend_id === selectedFriendId)}
                  onClick={() => {
                    if (selectedFriendId === '') return
                    const f = (friends ?? []).find((x) => x.friend_id === selectedFriendId)
                    if (!f) return
                    if (inviteQueue.some((q) => q.friend_id === f.friend_id)) return
                    setInviteQueue((prev) => [...prev, f])
                    setSelectedFriendId('')
                  }}
                  className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827] disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  Add
                </button>
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-end gap-3">
            <button
              onClick={async () => {
                const typeName = (useCustomType ? customTypeName : selectedClassName).trim()
                if (!typeName) return
                if (!title.trim()) return
                if (!startLocal || !endLocal) return
                const startDate = new Date(startLocal)
                const endDate = new Date(endLocal)
                if (!(startDate < endDate)) return
                const body: EventCreate = {
                  event_type: typeName,
                  header: header ?? undefined,
                  title: title,
                  start_time: new Date(startLocal).toISOString(),
                  end_time: new Date(endLocal).toISOString(),
                  color: color ?? undefined,
                  notes: notes ?? undefined,
                }
                try {
                  setSubmitting(true)
                  const created = await createEvent(body)
                  // Send invitations in sequence (could be parallel if needed)
                  for (const f of inviteQueue) {
                    try {
                      await createInvitation({ event_id: created.event_id, invited_user_id: f.friend_id })
                    } catch (e: any) {
                      const status = e?.response?.status
                      if (status === 400) show('Invalid invitation request', 'warning')
                      else if (status === 403) show('Not authorized to invite one or more users', 'error')
                      else if (status === 404) show('Event or user not found for an invite', 'warning')
                      else show('Failed to send one or more invitations', 'error')
                    }
                  }
                  onClose()
                  onCreated?.()
                } catch (e: any) {
                  const status = e?.response?.status
                  if (status === 400) show('Invalid event data', 'warning')
                  else if (status === 403) show('You are not authorized to create events', 'error')
                  else show('Failed to create event', 'error')
                } finally {
                  setSubmitting(false)
                }
              }}
              className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827] disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={(() => {
                const typeName = (useCustomType ? customTypeName : selectedClassName).trim()
                if (!typeName) return true
                if (!title.trim()) return true
                if (!startLocal || !endLocal) return true
                const startDate = new Date(startLocal)
                const endDate = new Date(endLocal)
                if (!(startDate < endDate)) return true
                return submitting
              })()}
            >
              {submitting ? 'Creating…' : 'Create'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}



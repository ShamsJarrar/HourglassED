import { useEffect, useMemo, useState } from 'react'
import type { EventResponse, InvitationStatus } from '../types/api'
import { getEventClasses, updateEvent, deleteEventById, type EventClassResponse } from '../lib/events'
import type { EventUpdate } from '../types/api'
import { getSentInvitations, getParticipants, type ParticipantResponse, createInvitation } from '../lib/invitations'
import { getFriendById, getFriendsList, type FriendsListResponseItem } from '../lib/friends'

type InvitationRow = {
  invitationId: number
  status: InvitationStatus | string
  userName: string
  userEmail: string
}

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
  const [invitations, setInvitations] = useState<InvitationRow[] | null>(null)
  const [participants, setParticipants] = useState<ParticipantResponse[] | null>(null)
  const [friends, setFriends] = useState<FriendsListResponseItem[] | null>(null)
  const [selectedFriendId, setSelectedFriendId] = useState<number | ''>('')
  const [inviteSubmitting, setInviteSubmitting] = useState(false)
  

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

  // Fetch invitations for owners when modal opens
  useEffect(() => {
    let isCancelled = false
    async function loadInvitations() {
      if (!open || !isOwner || !event) {
        setInvitations(null)
        return
      }
      setInvitations(null)
      try {
        const sent = await getSentInvitations({ event_id: event.event_id })
        const rows: InvitationRow[] = await Promise.all(
          sent.map(async (inv) => {
            const friendId = inv.invited_user_id
            if (friendId != null) {
              try {
                const f = await getFriendById(friendId)
                return {
                  invitationId: inv.invitation_id,
                  status: inv.status,
                  userName: f.friend_name,
                  userEmail: f.friend_email,
                }
              } catch {
                // fallback if friend fetch fails
              }
            }
            const email = inv.invited_user?.email
            return {
              invitationId: inv.invitation_id,
              status: inv.status,
              userName: email ? email.split('@')[0] : 'Unknown user',
              userEmail: email ?? '—',
            }
          })
        )
        if (!isCancelled) setInvitations(rows)
      } catch (e) {
        if (!isCancelled) setInvitations([])
      }
    }
    loadInvitations()
    return () => {
      isCancelled = true
    }
  }, [open, isOwner, event])

  // Fetch participants for non-owners when modal opens
  useEffect(() => {
    let isCancelled = false
    async function loadParticipants() {
      if (!open || isOwner || !event) {
        setParticipants(null)
        return
      }
      setParticipants(null)
      try {
        const res = await getParticipants(event.event_id)
        if (!isCancelled) setParticipants(res)
      } catch (e) {
        if (!isCancelled) setParticipants([])
      }
    }
    loadParticipants()
    return () => {
      isCancelled = true
    }
  }, [open, isOwner, event])

  // Fetch friends for owners when modal opens
  useEffect(() => {
    let isCancelled = false
    async function loadFriends() {
      if (!open || !isOwner) {
        setFriends(null)
        return
      }
      try {
        const list = await getFriendsList()
        if (!isCancelled) setFriends(list)
      } catch (e) {
        if (!isCancelled) setFriends([])
      }
    }
    loadFriends()
    return () => {
      isCancelled = true
    }
  }, [open, isOwner])

  if (!open || !event) return null

  const readOnly = !isOwner

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={onClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-[#633D00]">Event Details</h2>
          <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
        </div>

        <div className="space-y-3 text-[#633D00] flex-1 overflow-y-auto no-scrollbar">
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
          {isOwner && (
            <div className="pt-3 border-t border-[#633D00]/30">
              <label className="block text-sm font-medium mb-2">Invitations</label>
              {invitations === null ? (
                <div className="text-sm text-[#633D00]/70">Loading invitations…</div>
              ) : invitations.length === 0 ? (
                <div className="text-sm text-[#633D00]/70">No invitations sent.</div>
              ) : (
                <ul className="space-y-2">
                  {invitations.map((inv) => (
                    <li key={inv.invitationId} className="flex items-start justify-between gap-3 rounded-md border border-[#633D00]/30 bg-white px-3 py-2">
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{inv.userName}</div>
                        <div className="text-xs text-[#633D00]/70 truncate">{inv.userEmail}</div>
                      </div>
                      <div className="text-sm whitespace-nowrap">
                        <span className="text-[#633D00]/80">status: </span>
                        <span className="uppercase tracking-wide text-[#633D00]">{String(inv.status)}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              <div className="mt-3 flex items-center gap-2">
                <select
                  value={selectedFriendId === '' ? '' : String(selectedFriendId)}
                  onChange={(e) => setSelectedFriendId(e.target.value ? Number(e.target.value) : '')}
                  className="flex-1 rounded-md border border-[#633D00] px-3 py-2 bg-white"
                >
                  <option value="">Select a friend…</option>
                  {(friends ?? []).map((f) => (
                    <option key={f.friend_id} value={f.friend_id}>{`${f.friend_name} — ${f.friend_email}`}</option>
                  ))}
                </select>
                <button
                  disabled={inviteSubmitting || selectedFriendId === '' || !event}
                  onClick={async () => {
                    if (!event || selectedFriendId === '') return
                    try {
                      setInviteSubmitting(true)
                      await createInvitation({ event_id: event.event_id, invited_user_id: Number(selectedFriendId) })
                      // refresh invitations list
                      const sent = await getSentInvitations({ event_id: event.event_id })
                      const rows: InvitationRow[] = await Promise.all(
                        sent.map(async (inv) => {
                          const friendId = inv.invited_user_id
                          if (friendId != null) {
                            try {
                              const f = await getFriendById(friendId)
                              return { invitationId: inv.invitation_id, status: inv.status, userName: f.friend_name, userEmail: f.friend_email }
                            } catch {}
                          }
                          const email = inv.invited_user?.email
                          return { invitationId: inv.invitation_id, status: inv.status, userName: email ? email.split('@')[0] : 'Unknown user', userEmail: email ?? '—' }
                        })
                      )
                      setInvitations(rows)
                      setSelectedFriendId('')
                    } catch (e) {
                      // silently fail to UI; could add toast
                    } finally {
                      setInviteSubmitting(false)
                    }
                  }}
                  className="rounded-md bg-[#633D00] text-[#FAF0DC] px-4 py-2 hover:bg-[#765827] disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {inviteSubmitting ? 'Inviting…' : 'Invite'}
                </button>
              </div>
            </div>
          )}
          {!isOwner && (
            <div className="pt-3 border-t border-[#633D00]/30">
              <label className="block text-sm font-medium mb-2">Participants</label>
              {participants === null ? (
                <div className="text-sm text-[#633D00]/70">Loading participants…</div>
              ) : participants.length === 0 ? (
                <div className="text-sm text-[#633D00]/70">No participants found.</div>
              ) : (
                <ul className="space-y-2">
                  {participants.map((p, idx) => (
                    <li key={`${p.user_email}-${idx}`} className="flex items-start justify-between gap-3 rounded-md border border-[#633D00]/30 bg-white px-3 py-2">
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">
                          {p.user_name} {idx === 0 && <span className="text-xs text-[#633D00]/70">(Owner)</span>}
                        </div>
                        <div className="text-xs text-[#633D00]/70 truncate">{p.user_email}</div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        

        <div className="mt-8 flex justify-between gap-3">
          {isOwner && (
            <button
              onClick={async () => {
                if (!event) return
                if (!confirm('Delete this event? This cannot be undone.')) return
                try {
                  await deleteEventById(event.event_id)
                  onClose()
                } catch (e) {
                  console.error('Failed to delete event', e)
                }
              }}
              className="rounded-md border border-red-700 text-red-700 px-4 py-2 hover:bg-red-50"
            >
              Delete
            </button>
          )}
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
    </div>
  )
}



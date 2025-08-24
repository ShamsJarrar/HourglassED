import { useEffect, useMemo, useState } from 'react'
import type { EventResponse, InvitationStatus } from '../types/api'
import { getEventClasses, updateEvent, deleteEventById, type EventClassResponse, removeUserFromEvent, withdrawFromEvent } from '../lib/events'
import type { EventUpdate } from '../types/api'
import { getSentInvitations, getParticipants, type ParticipantResponse, createInvitation, cancelInvitation } from '../lib/invitations'
import { getFriendById, getFriendsList, type FriendsListResponseItem } from '../lib/friends'
import { useToast } from './Toast'

type InvitationRow = {
  invitationId: number
  status: InvitationStatus | string
  userName: string
  userEmail: string
  invitedUserId?: number | null
}

interface Props {
  event: EventResponse | null
  isOwner: boolean
  open: boolean
  onClose: () => void
  onSaved?: () => void
}

export default function EventModal({ event, isOwner, open, onClose }: Props) {
  const { show } = useToast()
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
  const [menuOpenFor, setMenuOpenFor] = useState<number | null>(null)
  const [actionLoadingFor, setActionLoadingFor] = useState<number | null>(null)
  const availableFriends = useMemo(() => {
    if (!friends) return [] as FriendsListResponseItem[]
    const blockedIds = new Set<number>()
    const blockedEmails = new Set<string>()
    ;(invitations ?? []).forEach((inv) => {
      const status = String(inv.status)
      if (status === 'pending' || status === 'accepted') {
        if (inv.invitedUserId != null) blockedIds.add(inv.invitedUserId)
        if (inv.userEmail) blockedEmails.add(inv.userEmail.toLowerCase())
      }
    })
    return friends.filter((f) => !blockedIds.has(f.friend_id) && !blockedEmails.has(f.friend_email.toLowerCase()))
  }, [friends, invitations])
  

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
    const ensureUtcIso = (value: string) => {
      // If backend sends naive ISO (no timezone), treat it as UTC
      return /([zZ]|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`
    }
    const toLocalInput = (iso: string) => {
      const d = new Date(ensureUtcIso(iso))
      const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      return local.toISOString().slice(0, 16)
    }
    setStartLocal(toLocalInput(event.start_time))
    setEndLocal(toLocalInput(event.end_time))
    
  }, [event, classNameById])

  // helper to load invitations and map to rows
  async function fetchAndSetInvitations(currentEvent: EventResponse) {
    const sent = await getSentInvitations({ event_id: currentEvent.event_id })
    const rows: InvitationRow[] = await Promise.all(
      sent.map(async (inv) => {
        let friendId = inv.invited_user_id
        if (friendId != null) {
          try {
            const f = await getFriendById(friendId)
            return {
              invitationId: inv.invitation_id,
              status: inv.status,
              userName: f.friend_name,
              userEmail: f.friend_email,
              invitedUserId: friendId,
            }
          } catch {}
        }
        const email = inv.invited_user?.email
        // Try to derive friend id from loaded friends list by email if available
        if (!friendId && email && friends && Array.isArray(friends)) {
          const match = friends.find((fr) => fr.friend_email.toLowerCase() === email.toLowerCase())
          if (match?.friend_id != null) {
            friendId = match.friend_id
          }
        }
        return {
          invitationId: inv.invitation_id,
          status: inv.status,
          userName: email ? email.split('@')[0] : 'Unknown user',
          userEmail: email ?? '—',
          invitedUserId: friendId ?? null,
        }
      })
    )
    setInvitations(rows)
  }

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
        if (!isCancelled) await fetchAndSetInvitations(event)
      } catch (e) {
        if (!isCancelled) setInvitations([])
      }
    }
    loadInvitations()
    return () => {
      isCancelled = true
    }
  }, [open, isOwner, event, friends])

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
          <h2 className="text-xl font-semibold text-[#633D00]">Event Details</h2>
          <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
        </div>

        <div className="space-y-3 text-[#633D00] flex-1 overflow-y-auto no-scrollbar">
          <div>
            <label className="block text-sm mb-1">Type *</label>
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
            <label className="text-sm mb-1 flex items-center">
              <span>Header</span>
              <img
                src="/icons/info_icon.svg"
                alt="info"
                title="Capitalized part of the title (max. 15 chars)"
                className="ml-1 h-4 w-4 opacity-80"
              />
            </label>
            <input maxLength={15} value={header ?? ''} onChange={(e) => setHeader(e.target.value)} disabled={readOnly} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
          </div>

          <div>
            <label className="block text-sm mb-1">Title *</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} disabled={readOnly} className="w-full rounded-md border border-[#633D00] px-3 py-2 bg-white" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm mb-1">Start *</label>
              {readOnly ? (
                <div className="rounded-md border border-[#633D00] px-3 py-2 bg-white">
                  {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(event.start_time))}
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
              <label className="block text-sm mb-1">End *</label>
              {readOnly ? (
                <div className="rounded-md border border-[#633D00] px-3 py-2 bg-white">
                  {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(event.end_time))}
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
            {!readOnly && (
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
            )}
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={(color?.startsWith('#') ? color : `#${color ?? 'ffffff'}`)}
                onChange={(e) => setColor(e.target.value)}
                disabled={readOnly}
                className="h-9 w-9 rounded-md border border-[#633D00] bg-white"
                title="Custom color"
                aria-label="Custom color"
              />
              {!readOnly && <span className="text-xs text-[#633D00]/70">Custom</span>}
            </div>
          </div>

          <div>
            <label className="block text-sm mb-1">Recurrence</label>
            <input disabled value="Not implemented yet" className="w-full rounded-md border border-[#633D00]/40 bg-[#f5efe2] px-3 py-2 text-[#633D00]/70" />
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
                    <li key={inv.invitationId} className="flex items-start justify-between gap-3 rounded-md border border-[#633D00]/30 bg-white px-3 py-2 relative">
                      <div className="min-w-0">
                        <div className="text-sm font-medium truncate">{inv.userName}</div>
                        <div className="text-xs text-[#633D00]/70 truncate">{inv.userEmail}</div>
                      </div>
                      <div className="text-sm whitespace-nowrap flex items-center gap-2">
                        <div>
                          <span className="text-[#633D00]/80">status: </span>
                          <span className="uppercase tracking-wide text-[#633D00]">{String(inv.status)}</span>
                        </div>
                        {(String(inv.status) === 'pending' || String(inv.status) === 'accepted') && (
                          <>
                            <button
                              className="p-1 hover:bg-[#633D00]/10 rounded"
                              onClick={() => setMenuOpenFor(menuOpenFor === inv.invitationId ? null : inv.invitationId)}
                              aria-label="More actions"
                            >
                              <img src="/icons/horizontal_dots_icon.svg" alt="actions" className="h-4 w-4" />
                            </button>
                            {menuOpenFor === inv.invitationId && (
                              <div className="absolute right-2 top-10 z-10 w-44 rounded-md border border-[#633D00]/30 bg-white shadow">
                                {String(inv.status) === 'pending' && (
                                  <button
                                    disabled={actionLoadingFor === inv.invitationId}
                                    onClick={async () => {
                                      if (!event) return
                                      try {
                                        setActionLoadingFor(inv.invitationId)
                                        await cancelInvitation(inv.invitationId)
                                        await fetchAndSetInvitations(event)
                                      } catch (e: any) {
                                        const status = e?.response?.status
                                        if (status === 403) show('Not authorized to cancel', 'error')
                                        else if (status === 404) show('Invitation not found', 'warning')
                                        else if (status === 400) show('Cannot cancel non-pending invite', 'warning')
                                        else show('Failed to cancel invite', 'error')
                                      }
                                      finally {
                                        setActionLoadingFor(null)
                                        setMenuOpenFor(null)
                                      }
                                    }}
                                    className="w-full text-left px-3 py-2 hover:bg-[#633D00]/10"
                                  >
                                    {actionLoadingFor === inv.invitationId ? 'Cancelling…' : 'Cancel invite'}
                                  </button>
                                )}
                                {String(inv.status) === 'accepted' && (
                                  <button
                                    disabled={actionLoadingFor === inv.invitationId || !inv.invitedUserId}
                                    onClick={async () => {
                                      if (!event || !inv.invitedUserId) return
                                      try {
                                        setActionLoadingFor(inv.invitationId)
                                        await removeUserFromEvent(event.event_id, inv.invitedUserId)
                                        await fetchAndSetInvitations(event)
                                      } catch (e: any) {
                                        const status = e?.response?.status
                                        if (status === 403) show('Not authorized to remove user', 'error')
                                        else if (status === 404) show('User not sharer or not found', 'warning')
                                        else show('Failed to remove user', 'error')
                                      }
                                      finally {
                                        setActionLoadingFor(null)
                                        setMenuOpenFor(null)
                                      }
                                    }}
                                    className="w-full text-left px-3 py-2 hover:bg-[#633D00]/10"
                                  >
                                    {actionLoadingFor === inv.invitationId ? 'Removing…' : 'Remove from event'}
                                  </button>
                                )}
                              </div>
                            )}
                          </>
                        )}
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
                  {availableFriends.map((f) => (
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
                      await fetchAndSetInvitations(event)
                      setSelectedFriendId('')
                    } catch (e: any) {
                      const status = e?.response?.status
                      if (status === 400) show('Invalid invitation request', 'warning')
                      else if (status === 403) show('You are not authorized to invite this user', 'error')
                      else if (status === 404) show('Event or user not found', 'warning')
                      else show('Failed to send invitation', 'error')
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
          {!isOwner && (
            <button
              onClick={async () => {
                if (!event) return
                if (!confirm('Withdraw from this event?')) return
                try {
                  await withdrawFromEvent(event.event_id)
                  onClose()
                } catch (e) {
                  console.error('Failed to withdraw', e)
                }
              }}
              className="rounded-md border border-red-700 text-red-700 px-4 py-2 hover:bg-red-50"
            >
              Withdraw
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



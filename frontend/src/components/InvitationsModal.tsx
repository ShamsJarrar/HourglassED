import { useEffect, useState, useMemo } from 'react'
import { getReceivedInvitations, respondToInvitation, type EventInvitationWithEvent } from '../lib/invitations'
import { getEventClasses, getEventClassById, type EventClassResponse } from '../lib/events'
import { useToast } from './Toast'

interface Props {
  open: boolean
  onClose: () => void
  onRefresh?: () => void
}

export default function InvitationsModal({ open, onClose, onRefresh }: Props) {
  const { show } = useToast()
  const [invitations, setInvitations] = useState<EventInvitationWithEvent[] | null>(null)
  const [loadingStates, setLoadingStates] = useState<Record<number, boolean>>({})
  const [classes, setClasses] = useState<EventClassResponse[]>([])
  const ensureUtcIso = (value: string) => (/([zZ]|[+-]\d{2}:?\d{2})$/.test(value) ? value : `${value}Z`)

  useEffect(() => {
    if (!open) return
    
    async function loadInvitations() {
      setInvitations(null)
      try {
        const received = await getReceivedInvitations()
        setInvitations(received)
        
        // Load event classes for displaying event type names
        try {
          const eventClasses = await getEventClasses()
          setClasses(eventClasses)
          
          // For each invitation, check if we need to fetch specific event classes
          const missingClassIds = new Set<number>()
          received.forEach(invitation => {
            const hasEventClass = eventClasses.some(c => c.class_id === invitation.event.event_type)
            if (!hasEventClass) {
              missingClassIds.add(invitation.event.event_type)
            }
          })
          
          // Fetch missing classes
          for (const classId of missingClassIds) {
            try {
              const specificClass = await getEventClassById(classId)
              setClasses(prev => [...prev, specificClass])
            } catch (error) {
              console.error('Failed to load specific event class:', error)
            }
          }
        } catch (error) {
          console.error('Failed to load event classes:', error)
        }
      } catch (e) {
        console.error('Failed to load invitations', e)
        show('Failed to load invitations', 'error')
        setInvitations([])
      }
    }
    
    loadInvitations()
  }, [open, show])

  const handleClose = () => {
    onClose()
    // Trigger refresh when modal is closed
    if (onRefresh) {
      onRefresh()
    }
  }

  const classNameById = useMemo(() => {
    const map = new Map<number, string>()
    classes.forEach(c => map.set(c.class_id, c.class_name))
    return map
  }, [classes])

  const formatTimeAgo = (dateString: string) => {
    const now = new Date()
    const date = new Date(dateString)
    const diffInMs = now.getTime() - date.getTime()
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes} min ago`
    if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`
    if (diffInDays < 7) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`
    return date.toLocaleDateString()
  }

  const handleRespond = async (invitationId: number, response: 'accepted' | 'rejected') => {
    setLoadingStates(prev => ({ ...prev, [invitationId]: true }))
    
    try {
      await respondToInvitation({ invitation_id: invitationId, response })
      
      // Remove the invitation from the list since it's no longer pending
      setInvitations(prev => prev?.filter(inv => inv.invitation_id !== invitationId) ?? [])
      
      show(
        response === 'accepted' ? 'Invitation accepted!' : 'Invitation rejected',
        'info'
      )
    } catch (e: any) {
      console.error('Failed to respond to invitation', e)
      const status = e?.response?.status
      if (status === 404) {
        show('Invitation not found', 'error')
      } else if (status === 403) {
        show('Not authorized to respond to this invitation', 'error')
      } else if (status === 400) {
        show('Invalid response or invitation already processed', 'error')
      } else {
        show('Failed to respond to invitation', 'error')
      }
    } finally {
      setLoadingStates(prev => ({ ...prev, [invitationId]: false }))
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={handleClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Event Invitations</h2>
            <button onClick={handleClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
          </div>

          <div className="flex-1 overflow-y-auto no-scrollbar">
            {invitations === null ? (
              <div className="text-center py-8">
                <div className="text-[#633D00]/70">Loading invitations...</div>
              </div>
            ) : invitations.length === 0 ? (
              <div className="text-center py-8">
                <div className="text-[#633D00]/70">No pending invitations</div>
              </div>
            ) : (
              <div className="space-y-3">
                {invitations.map((invitation) => (
                  <div key={invitation.invitation_id} className="rounded-md border border-[#633D00]/30 bg-white p-4 relative">
                    {/* Time ago indicator in top right */}
                    <div className="absolute top-2 right-2 text-xs text-[#633D00]/60">
                      {formatTimeAgo(invitation.created_at)}
                    </div>
                    
                    <div className="mb-3 pr-16">
                      <h3 className="font-semibold text-[#633D00] text-lg">{invitation.event.title}</h3>
                      {invitation.event.header && (
                        <p className="text-[#633D00]/70 text-sm">{invitation.event.header}</p>
                      )}
                    </div>
                    
                    <div className="space-y-2 text-sm text-[#633D00]/80">
                      <div>
                        <span className="font-medium">From:</span> {invitation.event.user.email}
                      </div>
                      <div>
                        <span className="font-medium">Type:</span> {classNameById.get(invitation.event.event_type) ?? '—'}
                      </div>
                      <div>
                        <span className="font-medium">Start:</span> {new Intl.DateTimeFormat(undefined, { 
                          dateStyle: 'medium', 
                          timeStyle: 'short' 
                        }).format(new Date(ensureUtcIso(invitation.event.start_time)))}
                      </div>
                      <div>
                        <span className="font-medium">End:</span> {new Intl.DateTimeFormat(undefined, { 
                          dateStyle: 'medium', 
                          timeStyle: 'short' 
                        }).format(new Date(ensureUtcIso(invitation.event.end_time)))}
                      </div>
                    </div>

                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={() => handleRespond(invitation.invitation_id, 'accepted')}
                        disabled={loadingStates[invitation.invitation_id]}
                        className="flex-1 rounded-md bg-green-600 text-white px-4 py-2 hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {loadingStates[invitation.invitation_id] ? 'Accepting...' : 'Accept'}
                      </button>
                      <button
                        onClick={() => handleRespond(invitation.invitation_id, 'rejected')}
                        disabled={loadingStates[invitation.invitation_id]}
                        className="flex-1 rounded-md bg-red-600 text-white px-4 py-2 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed"
                      >
                        {loadingStates[invitation.invitation_id] ? 'Rejecting...' : 'Reject'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

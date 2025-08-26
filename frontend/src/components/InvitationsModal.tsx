import { useEffect, useState } from 'react'
import { getReceivedInvitations, respondToInvitation, type EventInvitationWithEvent } from '../lib/invitations'
import { useToast } from './Toast'

interface Props {
  open: boolean
  onClose: () => void
}

export default function InvitationsModal({ open, onClose }: Props) {
  const { show } = useToast()
  const [invitations, setInvitations] = useState<EventInvitationWithEvent[] | null>(null)
  const [loadingStates, setLoadingStates] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!open) return
    
    async function loadInvitations() {
      setInvitations(null)
      try {
        const received = await getReceivedInvitations()
        setInvitations(received)
      } catch (e) {
        console.error('Failed to load invitations', e)
        show('Failed to load invitations', 'error')
        setInvitations([])
      }
    }
    
    loadInvitations()
  }, [open, show])

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
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/30" onClick={onClose}>
      <div className="w-[520px] max-w-[92vw] max-h-[86vh] rounded-xl bg-[#FFF8EB] border-2 border-[#633D00] shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="p-5 flex flex-col" style={{ maxHeight: '86vh' }}>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-[#633D00]">Event Invitations</h2>
            <button onClick={onClose} className="text-[#633D00] border border-[#633D00] rounded-md px-2 py-0.5">Close</button>
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
                  <div key={invitation.invitation_id} className="rounded-md border border-[#633D00]/30 bg-white p-4">
                    <div className="mb-3">
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
                        <span className="font-medium">Date:</span> {new Intl.DateTimeFormat(undefined, { 
                          dateStyle: 'medium', 
                          timeStyle: 'short' 
                        }).format(new Date(invitation.event.start_time))}
                      </div>
                      {invitation.event.notes && (
                        <div>
                          <span className="font-medium">Notes:</span> {invitation.event.notes}
                        </div>
                      )}
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

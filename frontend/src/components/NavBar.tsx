import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import InvitationsModal from './InvitationsModal'
import FriendsModal from './FriendsModal'

interface Props {
  onRefresh?: () => void
}

export default function NavBar({ onRefresh }: Props) {
  const navigate = useNavigate()
  const [invitationsModalOpen, setInvitationsModalOpen] = useState(false)
  const [friendsModalOpen, setFriendsModalOpen] = useState(false)

  return (
    <>
      <header className="w-full bg-[#633D00] text-[#FAF0DC] font-sans">
        <div className="mx-auto w-full pl-3 pr-7" style={{ height: 80 }}>
          <div className="grid h-full grid-cols-[auto_1fr_auto] items-center gap-x-12 lg:gap-x-16">
            {/* Left: Logo */}
            <div className="flex items-center shrink-0">
              <img src="/images/logo.png" alt="HourglassED" className="h-13 lg:h-17 w-auto shrink-0" />
            </div>

            {/* Middle: Empty space (removed tabs) */}
            <div className="flex items-center justify-start text-base lg:text-lg min-w-0">
              {/* Empty space where tabs used to be */}
            </div>

            {/* Right: Icons */}
            <div className="flex items-center gap-4 lg:gap-6 justify-end shrink-0">
              <button type="button" aria-label="Invitations" className="opacity-90 hover:opacity-150" onClick={() => setInvitationsModalOpen(true)}>
                <img src="/icons/invitations_icon.svg" alt="Invitations" className="h-5 w-5 lg:h-6 lg:w-6 shrink-0" />
              </button>
              <button type="button" aria-label="Friends" className="opacity-90 hover:opacity-150" onClick={() => setFriendsModalOpen(true)}>
                <img src="/icons/friends_icon.svg" alt="Friends" className="h-6 w-6 lg:h-7 lg:w-7 shrink-0" />
              </button>
              <button type="button" aria-label="Notifications" className="opacity-90 hover:opacity-150">
                <img src="/icons/notifications_icon.svg" alt="Notifications" className="h-5 w-5 lg:h-6 lg:w-6 shrink-0" />
              </button>
              <button
                type="button"
                aria-label="Logout"
                className="opacity-90 hover:opacity-150"
                onClick={() => {
                  try {
                    localStorage.removeItem('access_token')
                  } finally {
                    navigate('/login', { replace: true })
                  }
                }}
              >
                <img src="/icons/logout_icon.svg" alt="Logout" className="h-5 w-5 lg:h-6 lg:w-6 shrink-0" />
              </button>
            </div>
          </div>
        </div>
      </header>

      <InvitationsModal 
        open={invitationsModalOpen} 
        onClose={() => setInvitationsModalOpen(false)}
        onRefresh={onRefresh}
      />
      <FriendsModal 
        open={friendsModalOpen} 
        onClose={() => setFriendsModalOpen(false)}
        onRefresh={onRefresh}
      />
    </>
  )
}



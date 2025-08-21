import { Link, useLocation, useNavigate } from 'react-router-dom'

export default function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (path: string) => location.pathname === path

  return (
    <header className="w-full bg-[#633D00] text-[#FAF0DC] font-sans">
      <div className="mx-auto w-full pl-3 pr-7" style={{ height: 80 }}>
        <div className="grid h-full grid-cols-[auto_1fr_auto] items-center gap-x-12 lg:gap-x-16">
          {/* Left: Logo */}
          <div className="flex items-center shrink-0">
            <img src="/images/logo.png" alt="HourglassED" className="h-13 lg:h-17 w-auto shrink-0" />
          </div>

          {/* Middle: Tabs (towards center but slightly left due to grid layout) */}
          <nav className="flex items-center gap-10 lg:gap-15 justify-start text-base lg:text-lg min-w-0 overflow-x-auto whitespace-nowrap">
            <Link
              to="/"
              className={`transition-opacity ${isActive('/') ? 'opacity-100 font-bold' : 'opacity-90 hover:opacity-150'}`}
            >
              Calendar
            </Link>
            <Link
              to="/invitations"
              className={`transition-opacity ${isActive('/invitations') ? 'opacity-100 font-semibold' : 'opacity-90 hover:opacity-150'}`}
            >
              Invitations
            </Link>
            <Link
              to="/friends"
              className={`transition-opacity ${isActive('/friends') ? 'opacity-100 font-semibold' : 'opacity-90 hover:opacity-150'}`}
            >
              Friends
            </Link>
          </nav>

          {/* Right: Icons */}
          <div className="flex items-center gap-4 lg:gap-6 justify-end shrink-0">
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
  )
}



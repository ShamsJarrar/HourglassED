'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';

export default function Navbar() {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  const handleLogout = () => {
    // Implement logout functionality
  };

  return (
    <header className="w-full h-[104px] bg-[var(--brand)] relative">
      {/* Logo */}
      <div className="absolute top-0.5 left-[13px] w-[346px] h-[103px]">
        <Link href="/calendar">
          <Image
            src="/logo/logo.png"
            alt="HourglassED Logo"
            width={346}
            height={103}
            className="object-cover"
          />
        </Link>
      </div>

      {/* Navigation tabs */}
      <nav
        className="absolute w-[706px] h-10 top-8 left-[403px]"
        role="navigation"
        aria-label="Main navigation"
      >
        <Link
          href="/calendar"
          className={`absolute w-[235px] h-10 top-0 left-0 text-[var(--text-on-brand)] text-[29px] text-center tracking-[0] leading-[normal] transition-all duration-200 ${
            isActive('/calendar') ? "font-bold border-b-2 border-[var(--text-on-brand)]" : "font-normal"
          } hover:font-bold flex items-center justify-center`}
          aria-current={isActive('/calendar') ? "page" : undefined}
        >
          Calendar
        </Link>
        
        <Link
          href="/invitations"
          className={`absolute w-[235px] h-10 top-0 left-[235px] text-[var(--text-on-brand)] text-[29px] text-center tracking-[0] leading-[normal] transition-all duration-200 ${
            isActive('/invitations') ? "font-bold border-b-2 border-[var(--text-on-brand)]" : "font-normal"
          } hover:font-bold flex items-center justify-center`}
          aria-current={isActive('/invitations') ? "page" : undefined}
        >
          Invitations
        </Link>
        
        <Link
          href="/friends"
          className={`absolute w-[235px] h-10 top-0 left-[470px] text-[var(--text-on-brand)] text-[29px] text-center tracking-[0] leading-[normal] transition-all duration-200 ${
            isActive('/friends') ? "font-bold border-b-2 border-[var(--text-on-brand)]" : "font-normal"
          } hover:font-bold flex items-center justify-center`}
          aria-current={isActive('/friends') ? "page" : undefined}
        >
          Friends
        </Link>
      </nav>

      {/* Right side icons */}
      <div className="absolute top-[34px] right-[50px] flex items-center gap-[51px]">
        <button
          className="hover:opacity-80 transition-opacity duration-200"
          aria-label="View notifications"
        >
          <Image
            src="/icons/notifications_icon.svg"
            alt=""
            width={29}
            height={36}
          />
        </button>

        <button
          onClick={handleLogout}
          className="hover:opacity-80 transition-opacity duration-200"
          aria-label="Logout"
        >
          <Image
            src="/icons/logout_icon.svg"
            alt=""
            width={39}
            height={39}
          />
        </button>
      </div>
    </header>
  );
}
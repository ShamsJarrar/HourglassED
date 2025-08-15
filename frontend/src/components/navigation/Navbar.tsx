'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Image from 'next/image';

interface NavbarProps {
  notificationCount?: number;
}

export default function Navbar({ notificationCount = 0 }: NavbarProps) {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  const handleLogout = () => {
    // TODO: Implement logout functionality
    console.log('Logout clicked');
  };

  return (
    <nav style={{ backgroundColor: '#633D00' }} className="h-14 px-8 w-full">
      <div className="w-full h-full flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center">
          <Link href="/calendar" className="flex items-center gap-3">
            <Image 
              src="/logo/logo.png" 
              alt="HourglassED" 
              width={150} 
              height={40}
              className="h-8 w-auto"
            />
          </Link>
        </div>

        {/* Navigation Links - Centered */}
        <div className="flex items-center space-x-8 absolute left-1/2 transform -translate-x-1/2">
          <Link
            href="/calendar"
            className={`text-base transition-all duration-200 ${
              isActive('/calendar') 
                ? 'font-bold' 
                : 'font-normal hover:font-medium'
            }`}
            style={{ color: '#FAF0DC' }}
          >
            Calendar
          </Link>

          <Link
            href="/invitations"
            className={`text-base transition-all duration-200 ${
              isActive('/invitations') 
                ? 'font-bold' 
                : 'font-normal hover:font-medium'
            }`}
            style={{ color: '#FAF0DC' }}
          >
            Invitations
          </Link>

          <Link
            href="/friends"
            className={`text-base transition-all duration-200 ${
              isActive('/friends') 
                ? 'font-bold' 
                : 'font-normal hover:font-medium'
            }`}
            style={{ color: '#FAF0DC' }}
          >
            Friends
          </Link>
        </div>

        {/* Right side: Notifications & Logout */}
        <div className="flex items-center space-x-4">
          {/* Notification Bell */}
          <button className="hover:opacity-80 transition-opacity duration-200">
            <Image 
              src="/icons/notifications_icon.svg" 
              alt="Notifications" 
              width={24} 
              height={24}
              className="w-6 h-6"
            />
          </button>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="hover:opacity-80 transition-opacity duration-200"
          >
            <Image 
              src="/icons/logout_icon.svg" 
              alt="Logout" 
              width={24} 
              height={24}
              className="w-6 h-6"
            />
          </button>
        </div>
      </div>
    </nav>
  );
}
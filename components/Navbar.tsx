'use client';

import { Bell, LogOut } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="h-16 bg-[var(--brand)] text-[var(--text-on-brand)] flex items-center justify-between px-6">
      {/* Left side - could be logo/brand */}
      <div></div>
      
      {/* Center - Navigation tabs */}
      <div className="flex items-center space-x-8">
        <button className="text-[var(--text-on-brand)] hover:opacity-80 transition-opacity">
          Calendar
        </button>
        <button className="text-[var(--text-on-brand)] hover:opacity-80 transition-opacity">
          Invitations
        </button>
        <button className="text-[var(--text-on-brand)] hover:opacity-80 transition-opacity">
          Friends
        </button>
      </div>
      
      {/* Right side - Bell and Logout */}
      <div className="flex items-center space-x-4">
        <button className="text-[var(--text-on-brand)] hover:opacity-80 transition-opacity">
          <Bell size={20} />
        </button>
        <button className="text-[var(--text-on-brand)] hover:opacity-80 transition-opacity">
          <LogOut size={20} />
        </button>
      </div>
    </nav>
  );
}

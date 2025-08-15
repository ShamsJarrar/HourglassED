'use client';

import { Plus, Calendar, Settings, Users } from 'lucide-react';

export default function ToolsRail() {
  return (
    <div className="w-60 bg-[var(--surface)] border border-[var(--border-muted)] p-4 rounded-lg">
      {/* Primary Action Button */}
      <button className="w-full h-12 bg-[var(--brand)] text-[var(--text-on-brand)] rounded-xl flex items-center justify-center gap-2 shadow-sm hover:shadow-md transition-shadow mb-4">
        <Plus size={18} />
        <span>New Event</span>
      </button>
      
      {/* Secondary Buttons */}
      <div className="space-y-2">
        <button className="w-full h-12 bg-white border border-[var(--border-muted)] text-gray-700 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors">
          <Calendar size={18} />
          <span>My Calendar</span>
        </button>
        
        <button className="w-full h-12 bg-white border border-[var(--border-muted)] text-gray-700 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors">
          <Users size={18} />
          <span>Shared</span>
        </button>
        
        <button className="w-full h-12 bg-white border border-[var(--border-muted)] text-gray-700 rounded-xl flex items-center justify-center gap-2 hover:bg-gray-50 transition-colors">
          <Settings size={18} />
          <span>Settings</span>
        </button>
      </div>
    </div>
  );
}

'use client';

export default function CalendarSurface() {
  return (
    <div className="bg-[var(--surface)] border border-[var(--border-muted)] rounded-[20px] p-6 flex items-center justify-center min-h-[600px]">
      <div className="text-center text-gray-500">
        <h2 className="text-2xl font-medium mb-2">Calendar Area</h2>
        <p className="text-gray-400">Your calendar view will be displayed here</p>
      </div>
    </div>
  );
}

import Image from 'next/image';

export default function CalendarPage() {
  return (
    <div className="h-full flex" style={{ backgroundColor: '#FFF8EB', minHeight: 'calc(100vh - 56px)' }}>
      {/* Left Sidebar - Tools Section */}
      <div 
        className="w-72 p-6 space-y-4 border-r"
        style={{ borderColor: '#D1D5DB' }}
      >
        {/* Create Button */}
        <button 
          className="w-full flex items-center gap-3 px-6 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:opacity-90"
          style={{ backgroundColor: '#633D00', color: '#FAF0DC' }}
        >
          <Image 
            src="/icons/plus_icon.svg" 
            alt="Create" 
            width={20} 
            height={20}
            className="w-5 h-5"
          />
          Create
        </button>

        {/* Month Dropdown */}
        <button 
          className="w-full flex items-center justify-between px-5 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:opacity-90"
          style={{ backgroundColor: '#FAF0DC', color: '#633D00' }}
        >
          <span>Month</span>
          <Image 
            src="/icons/down_icon.svg" 
            alt="Dropdown" 
            width={16} 
            height={16}
            className="w-4 h-4"
          />
        </button>

        {/* Today Button */}
        <button 
          className="w-full px-5 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:opacity-90 text-left"
          style={{ backgroundColor: '#FAF0DC', color: '#633D00' }}
        >
          Today
        </button>

        {/* Filter Button */}
        <button 
          className="w-full flex items-center gap-3 px-5 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:opacity-90"
          style={{ backgroundColor: '#FAF0DC', color: '#633D00' }}
        >
          <Image 
            src="/icons/filter_icon.svg" 
            alt="Filter" 
            width={20} 
            height={20}
            className="w-5 h-5"
          />
          Filter
        </button>

        {/* Organize with Agent Button */}
        <button 
          className="w-full px-5 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:opacity-90 mt-8 text-left"
          style={{ backgroundColor: '#633D00', color: '#FAF0DC' }}
        >
          Organize with Agent
        </button>
      </div>

      {/* Main Calendar Area */}
      <div className="flex-1 p-6">
        <div 
          className="w-full h-full rounded-xl border"
          style={{ 
            backgroundColor: '#FAF0DC', 
            borderColor: '#D1D5DB',
            minHeight: 'calc(100vh - 112px)' // Ensure it fills properly
          }}
        >
          {/* Calendar will be implemented here */}
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-5xl mb-4">📅</div>
              <h3 className="text-xl font-semibold mb-3" style={{ color: '#633D00' }}>
                Calendar Area
              </h3>
              <p style={{ color: '#633D00' }} className="opacity-70">
                FullCalendar will be integrated here
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
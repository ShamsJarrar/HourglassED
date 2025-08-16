'use client';

export default function CalendarSurface() {
  return (
    <main
      className="absolute w-[1230px] h-[878px] top-[104px] left-[282px] border border-solid border-[#dbdbdb]"
      role="main"
      aria-label="Calendar content"
    >
      <div className="relative w-[1202px] h-[847px] top-[15px] left-3.5 bg-[#fff8eb] rounded-[30px] border border-solid border-[#c1c1c1] flex items-center justify-center">
        <div className="text-center text-gray-500">
          <h2 className="text-2xl font-medium mb-2">Calendar Area</h2>
          <p className="text-gray-400">Your calendar view will be displayed here</p>
        </div>
      </div>
    </main>
  );
}

'use client';

import Image from 'next/image';

const sidebarButtons = [
  {
    id: "create",
    label: "Create",
    type: "primary",
    icon: "/icons/plus_icon.svg",
  },
  {
    id: "month",
    label: "Month",
    type: "secondary",
    icon: "/icons/down_icon.svg",
  },
  {
    id: "today",
    label: "Today",
    type: "secondary",
  },
  {
    id: "filter",
    label: "Filter",
    type: "secondary",
    icon: "/icons/filter_icon.svg",
  },
  {
    id: "organize",
    label: "Organize with Agent",
    type: "primary",
  },
];

export default function ToolsRail() {
  const handleButtonClick = (buttonId: string) => {
    // Handle button functionality here
  };

  return (
    <aside
      className="absolute w-[282px] h-[878px] top-[104px] left-0 border border-solid border-[#dbdbdb]"
      role="complementary"
      aria-label="Sidebar navigation"
    >
      {sidebarButtons.map((button) => {
        const positions = {
          create: { top: 120, left: 23, width: 237, height: 86 },
          month: { top: 240, left: 23, width: 199, height: 66 },
          today: { top: 330, left: 23, width: 199, height: 66 },
          filter: { top: 420, left: 23, width: 199, height: 66 },
          organize: { top: 540, left: 14, width: 254, height: 86 },
        };

        const pos = positions[button.id as keyof typeof positions];

        if (button.type === "primary") {
          return (
            <button
              key={button.id}
              onClick={() => handleButtonClick(button.id)}
              className="absolute hover:opacity-90 transition-opacity duration-200 focus:ring-2 focus:ring-[#faf0dc] focus:ring-offset-2 focus:ring-offset-[#fff8eb]"
              style={{
                top: `${pos.top}px`,
                left: `${pos.left}px`,
                width: `${pos.width}px`,
                height: `${pos.height}px`,
              }}
              aria-label={button.label}
            >
              <div
                className={`relative h-[86px] ${
                  button.id === "organize" 
                    ? "w-[254px]" 
                    : "w-[235px] bg-[#623c00] rounded-[15px] shadow-[0px_4px_4px_#00000040]"
                }`}
              >
                {button.id === "organize" && (
                  <div className="absolute w-[235px] h-[86px] top-0 left-[9px] bg-[#623c00] rounded-[15px] shadow-[0px_4px_4px_#00000040]" />
                )}
                <div
                  className={`absolute h-[43px] top-[21px] font-medium text-[#faf0dc] text-center tracking-[0] leading-[normal] flex items-center justify-center ${
                    button.id === "organize"
                      ? "w-[254px] left-0 text-[20px]"
                      : "w-[150px] left-[60px] text-[24px]"
                  }`}
                >
                  {button.label}
                </div>
                {button.icon && button.id === "create" && (
                  <Image
                    src={button.icon}
                    alt=""
                    width={24}
                    height={24}
                    className="absolute w-[24px] h-[24px] top-[31px] left-8"
                  />
                )}
              </div>
            </button>
          );
        } else {
          return (
            <button
              key={button.id}
              onClick={() => handleButtonClick(button.id)}
              className="absolute hover:bg-[#f5f5f5] transition-colors duration-200 focus:ring-2 focus:ring-[#623c00] focus:ring-offset-2 focus:ring-offset-[#fff8eb]"
              style={{
                top: `${pos.top}px`,
                left: `${pos.left}px`,
                width: `${pos.width}px`,
                height: `${pos.height}px`,
              }}
              aria-label={button.label}
            >
              <div className="relative w-[197px] h-[66px] rounded-[11.51px]">
                <div
                  className={`absolute h-[66px] top-0 font-normal text-[#623c00] text-[22px] text-center tracking-[0] leading-[normal] flex items-center justify-center ${
                    button.icon
                      ? "w-[130px] left-[50px]"
                      : "w-[130px] left-[35px]"
                  }`}
                >
                  {button.label}
                </div>
                <div className="absolute w-[197px] h-[66px] top-0 left-0 rounded-[11.51px] border border-solid border-[#623c00]" />
                {button.icon && (
                  <Image
                    src={button.icon}
                    alt=""
                    width={button.id === "month" ? 20 : 20}
                    height={button.id === "month" ? 20 : 20}
                    className={`absolute ${
                      button.id === "month"
                        ? "w-5 h-5 left-6 top-1/2 transform -translate-y-1/2"
                        : "w-5 h-5 left-6 top-1/2 transform -translate-y-1/2"
                    }`}
                  />
                )}
              </div>
            </button>
          );
        }
      })}
    </aside>
  );
}

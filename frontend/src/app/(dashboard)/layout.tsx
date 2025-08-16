interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="bg-[#fff8eb] flex justify-center items-start min-h-screen w-full">
      <div className="bg-[#fff8eb] w-[1512px] h-[982px] relative overflow-hidden">
        {children}
      </div>
    </div>
  );
}

import Navbar from '@/components/Navbar';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--surface)]">
      <Navbar />
      <main className="p-6">
        <div className="grid grid-cols-[240px_1fr] gap-4">
          {children}
        </div>
      </main>
    </div>
  );
}

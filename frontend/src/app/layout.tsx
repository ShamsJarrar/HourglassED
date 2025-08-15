import type { Metadata } from "next";
import { Instrument_Sans } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/navigation/Navbar";

const instrumentSans = Instrument_Sans({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "HourglassED - Academic Calendar & Study Planner",
  description: "A comprehensive academic calendar and study planning application for students",
  icons: {
    icon: '/logo/logo_icon.svg',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={instrumentSans.className}>
        <div className="min-h-screen" style={{ backgroundColor: '#FFF8EB' }}>
          {/* Only show navbar on non-auth pages */}
          <ConditionalNavbar />
          
          {/* Main content */}
          <main className="h-full">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}

function ConditionalNavbar() {
  // We'll implement auth context later to check if user is logged in
  // For now, we'll show navbar on all pages except auth pages
  return <Navbar />; // Remove mock notification count
}
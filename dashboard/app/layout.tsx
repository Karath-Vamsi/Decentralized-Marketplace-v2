import type { Metadata } from "next";
import { Geist, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Web3Provider } from "@/providers/Web3Provider";
import CinematicBackground from "@/components/CinematicBackground";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";

const geistSans = Geist({ 
  variable: "--font-geist-sans", 
  subsets: ["latin"] 
});

const playfair = Playfair_Display({ 
  variable: "--font-serif-premium", 
  subsets: ["latin"], 
  style: ['italic'],
  weight: ['400']
});

export const metadata: Metadata = {
  title: "AISAAS | Decentralized Intelligence Marketplace",
  description: "Sovereign Intelligence Architecture // Spatial OS v4.0",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark no-select">
      <body className={`${geistSans.variable} ${playfair.variable} antialiased selection:bg-brand-accent selection:text-brand-bg`}>
        {/* --- VISUAL FOUNDATION LAYERS --- */}
        <CinematicBackground />
        <div className="linear-grid" />
        <div className="noise-overlay" />
        
        {/* --- LOGIC PROVIDERS (PRESERVED) --- */}
        <Web3Provider>
          <TooltipProvider delayDuration={0}>
            {/* Main Content Area: High Z-Index to stay above backgrounds */}
            <main className="relative z-10 min-h-screen">
              {children}
            </main>

            {/* Premium Notification System (Linear/Stripe style) */}
            <Toaster 
              theme="dark"
              position="bottom-right"
              toastOptions={{
                className: 'glass-forest border-white/10 text-brand-text font-sans',
              }}
            />
          </TooltipProvider>
        </Web3Provider>
      </body>
    </html>
  );
}
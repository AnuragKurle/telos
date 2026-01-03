import { Hero } from "@/components/Hero";
import { Features } from "@/components/Features";
import { HowItWorks } from "@/components/HowItWorks";
import { WaitlistCTA } from "@/components/WaitlistCTA";
import { Terminal, Twitter } from "lucide-react";

export default function Home() {
  return (
    <main className="min-h-screen bg-terminal-black flex flex-col">
      {/* Navigation / Header */}
      <header className="fixed top-0 w-full z-50 bg-terminal-black/80 backdrop-blur-md border-b border-terminal-border">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 text-white font-bold text-xl tracking-tight">
            <Terminal className="w-6 h-6 text-terminal-green" />
            <span>telos</span>
          </div>
          <a
            href="#waitlist"
            className="px-4 py-2 text-sm font-medium text-terminal-green border border-terminal-green/30 rounded-md hover:bg-terminal-green/10 transition-colors"
          >
            Get Early Access
          </a>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 pt-16">
        <Hero />
        <Features />
        <HowItWorks />
        <div id="waitlist">
          <WaitlistCTA />
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-terminal-border bg-neutral-950 py-12 px-4">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2 text-neutral-500">
            <Terminal className="w-5 h-5" />
            <span className="text-sm">© {new Date().getFullYear()} Telos. Know where your time goes.</span>
          </div>

          <div className="flex items-center gap-6">
            <a href="#" className="text-neutral-500 hover:text-white transition-colors">
              <Twitter className="w-5 h-5" />
            </a>
          </div>
        </div>
      </footer>
    </main>
  );
}

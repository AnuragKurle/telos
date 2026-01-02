import React from "react";
import { cn } from "@/lib/utils";

interface TerminalFrameProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function TerminalFrame({ title = "telos-client", children, className }: TerminalFrameProps) {
  return (
    <div className={cn("rounded-lg border border-terminal-border bg-terminal-black shadow-2xl overflow-hidden font-mono", className)}>
      {/* Title Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-neutral-900 border-b border-terminal-border">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <div className="text-xs text-neutral-500 font-medium select-none">{title}</div>
        <div className="w-16" /> {/* Spacer for centering */}
      </div>
      
      {/* Content */}
      <div className="p-4 relative">
         {/* Scanline Effect Overlay (Optional, low opacity) */}
         <div className="absolute inset-0 pointer-events-none opacity-[0.03] scanline z-10" />
         
         <div className="relative z-0">
           {children}
         </div>
      </div>
    </div>
  );
}


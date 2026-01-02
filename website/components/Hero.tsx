"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { ChevronRight, Loader2, Check } from "lucide-react";
import { TypewriterEffect } from "./TypewriterEffect";
import { TerminalFrame } from "./TerminalFrame";
import { db } from "@/lib/firebase";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

export function Hero() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || status === "loading") return;

    setStatus("loading");
    setErrorMsg("");

    try {
      // Use email as document ID to prevent duplicates
      const safeEmail = email.toLowerCase().trim();
      await setDoc(doc(db, "waitlist", safeEmail), {
        email: safeEmail,
        timestamp: serverTimestamp(),
        source: "landing_page",
      });
      setStatus("success");
      setEmail("");
    } catch (error: any) {
      console.error("Error adding to waitlist:", error);
      setStatus("error");
      setErrorMsg(error?.message || "Connection failed");
    }
  };

  return (
    <section className="relative min-h-screen flex flex-col justify-center items-center px-4 py-20 overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="z-10 text-center max-w-4xl mx-auto mb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-terminal-green/10 border border-terminal-green/20 text-terminal-green text-xs font-medium mb-6"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-terminal-green opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-terminal-green"></span>
          </span>
          Phase 1: The Observer Available Now
        </motion.div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
          Protect Your <span className="text-terminal-green">Intentions</span>
          <br />
          <span className="text-neutral-500 font-mono text-2xl md:text-4xl mt-2 block">
            <TypewriterEffect text={["Fight the algorithm.", "Defend your focus.", "Align your time.", "Zero overhead."]} />
          </span>
        </h1>

        <p className="text-neutral-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          The terminal-based productivity assistant that aligns your screen time with your goals.
          <br className="hidden md:block" />
          A lightweight guardian against algorithmic distraction.
        </p>

        {/* Email CTA */}
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 justify-center items-center max-w-md mx-auto w-full">
          <div className="relative w-full">
             <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-neutral-500 font-mono text-sm">
                $
             </div>
             <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="enter_email_for_access" 
                required
                disabled={status === "loading" || status === "success"}
                className="w-full pl-8 pr-4 py-3 bg-neutral-900 border border-neutral-800 rounded-md focus:outline-none focus:border-terminal-green focus:ring-1 focus:ring-terminal-green text-white font-mono placeholder:text-neutral-600 transition-all disabled:opacity-50"
             />
          </div>
          <button 
            type="submit"
            disabled={status === "loading" || status === "success"}
            className="w-full sm:w-auto px-6 py-3 bg-terminal-green text-black font-semibold rounded-md hover:bg-emerald-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed min-w-[140px]"
          >
            {status === "loading" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : status === "success" ? (
              <>
                Joined <Check className="w-4 h-4" />
              </>
            ) : (
              <>
                Join Waitlist <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
        {status === "error" && (
            <div className="text-xs text-red-500 mt-4 font-mono bg-red-950/30 px-3 py-2 rounded border border-red-900/50">
              Error: {errorMsg || "Connection failed. Check your network."}
            </div>
        )}
        <p className="text-xs text-neutral-600 mt-4">
          Privacy-first architecture. Your data stays on your device.
        </p>
      </div>

      {/* Terminal Demo */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="w-full max-w-5xl z-10"
      >
        <TerminalFrame title="telos — guardian_mode">
          <div className="font-mono text-sm md:text-base space-y-4">
            <div className="flex gap-2">
              <span className="text-terminal-green">➜</span>
              <span className="text-blue-400">~</span>
              <span className="text-white">telos intent set "Deep work on backend architecture"</span>
            </div>
            
            <div className="pl-4 border-l-2 border-neutral-800 space-y-4">
              <div className="text-neutral-400">Intention locked. Monitoring distraction vectors...</div>
              
              <div className="opacity-50 text-xs text-neutral-600 italic">
                [+20 mins passed]
              </div>

              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="text-terminal-amber font-bold">Guardian:</span>
                  <div className="text-neutral-300">
                    <p className="mb-2 text-terminal-amber">⚠️ Alignment Alert</p>
                    <p>You intended to work on <span className="text-white font-semibold">backend architecture</span>.</p>
                    <p className="text-neutral-400 mt-1">
                      Current activity: <span className="text-red-400">Twitter/X (15m)</span>, <span className="text-red-400">Hacker News (5m)</span>.
                    </p>
                    <p className="mt-2 font-bold text-white">Resuming focus protocol? [Y/n]</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-2">
              <span className="text-terminal-green">➜</span>
              <span className="text-blue-400">~</span>
              <span className="w-2 h-5 bg-white animate-pulse inline-block align-middle" />
            </div>
          </div>
        </TerminalFrame>
      </motion.div>
    </section>
  );
}

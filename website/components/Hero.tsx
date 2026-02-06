"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronRight, Loader2, Check, Monitor, Apple } from "lucide-react";
import { TypewriterEffect } from "./TypewriterEffect";
import { TerminalFrame } from "./TerminalFrame";
import { db } from "@/lib/firebase";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

export function Hero() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [referralCode, setReferralCode] = useState<string | null>(null);

  // Capture referral code from URL on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      const ref = params.get("ref");
      if (ref && ref.startsWith("TELOS-")) {
        setReferralCode(ref);
        // Store in localStorage for persistence across page navigations
        localStorage.setItem("telos_referral_code", ref);
      } else {
        // Check localStorage for previously stored referral code
        const stored = localStorage.getItem("telos_referral_code");
        if (stored && stored.startsWith("TELOS-")) {
          setReferralCode(stored);
        }
      }
    }
  }, []);

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
        source: referralCode ? `referral_${referralCode}` : "landing_page",
        ...(referralCode && { referralCode }),
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
          className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-neutral-900/80 border border-neutral-800 text-neutral-400 text-xs font-medium mb-6"
        >
          <span className="flex items-center gap-1.5">
            <Monitor className="w-3.5 h-3.5" />
            Windows
          </span>
          <span className="text-neutral-700">•</span>
          <span className="flex items-center gap-1.5">
            <Apple className="w-3.5 h-3.5" />
            macOS
          </span>
        </motion.div>

        <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
          Know Exactly Where Your <span className="text-terminal-green">Time Goes</span>
          <br />
          <span className="text-neutral-500 font-mono text-2xl md:text-4xl mt-2 block">
            <TypewriterEffect text={["What did I do today?", "How long was that meeting?", "When did I finish that task?", "Where did my morning go?"]} />
          </span>
        </h1>

        <p className="text-neutral-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed">
          Automatic time tracking that shows you what you <em>actually</em> did.
          <br className="hidden md:block" />
          Screenshots never stored. Data encrypted. Ask questions in plain English.
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
              placeholder="your@email.com"
              required
              disabled={status === "loading" || status === "success"}
              className="w-full pl-8 pr-4 py-3 bg-neutral-900 border border-neutral-800 rounded-md focus:outline-none focus:border-terminal-green focus:ring-1 focus:ring-terminal-green text-white font-mono placeholder:text-neutral-600 transition-all disabled:opacity-50"
            />
          </div>
          <button
            type="submit"
            disabled={status === "loading" || status === "success"}
            className="w-full sm:w-auto px-6 py-3 bg-terminal-green text-black font-semibold rounded-md hover:bg-emerald-400 transition-colors flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed min-w-[160px]"
          >
            {status === "loading" ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : status === "success" ? (
              <>
                You're In! <Check className="w-4 h-4" />
              </>
            ) : (
              <>
                Get Started <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
        {status === "error" && (
          <div className="text-xs text-red-500 mt-4 font-mono bg-red-950/30 px-3 py-2 rounded border border-red-900/50">
            Error: {errorMsg || "Connection failed. Check your network."}
          </div>
        )}
        {referralCode ? (
          <p className="text-xs text-neutral-400 mt-4">
            <span className="text-purple-400">Referred by a friend</span> • <span className="text-terminal-green font-semibold">14-day extended trial</span> • Then $3/month
          </p>
        ) : (
          <p className="text-xs text-neutral-600 mt-4">
            7-day free trial • Then $3/month • Installs in 30 seconds
          </p>
        )}
      </div>

      {/* Terminal Demo */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="w-full max-w-5xl z-10"
      >
        <TerminalFrame title="telos — dashboard">
          <div className="font-mono text-sm md:text-base space-y-4">
            <div className="flex gap-2">
              <span className="text-terminal-green">➜</span>
              <span className="text-blue-400">~</span>
              <span className="text-white">telos chat "What did I work on this morning?"</span>
            </div>

            <div className="pl-4 border-l-2 border-neutral-800 space-y-3">
              <div className="text-neutral-300">
                <p className="text-terminal-green mb-2">📊 This morning (9am - 12pm):</p>
                <div className="space-y-1 text-sm">
                  <p><span className="text-blue-400">2h 15m</span> — VS Code: Working on API refactor</p>
                  <p><span className="text-terminal-amber">35m</span> — Browser: Stack Overflow, GitHub docs</p>
                  <p><span className="text-red-400">10m</span> — Slack: Team messages</p>
                </div>
                <p className="mt-3 text-neutral-400 text-sm">You completed the auth middleware and started on rate limiting.</p>
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

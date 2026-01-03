"use client";

import { useState } from "react";
import { ChevronRight, Loader2, Check, Users } from "lucide-react";
import { db } from "@/lib/firebase";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

export function WaitlistCTA() {
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [errorMsg, setErrorMsg] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email || status === "loading") return;

        setStatus("loading");
        setErrorMsg("");

        try {
            const safeEmail = email.toLowerCase().trim();
            await setDoc(doc(db, "waitlist", safeEmail), {
                email: safeEmail,
                timestamp: serverTimestamp(),
                source: "landing_page_bottom",
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
        <section className="py-20 px-4 bg-gradient-to-b from-neutral-950 to-neutral-900 border-t border-neutral-800">
            <div className="max-w-2xl mx-auto text-center">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-terminal-green/10 border border-terminal-green/20 text-terminal-green text-sm font-medium mb-6">
                    <Users className="w-4 h-4" />
                    <span>Join 80+ people on the waitlist</span>
                </div>

                <h2 className="text-3xl md:text-4xl font-bold mb-4">
                    Ready to Know Where Your Time Goes?
                </h2>
                <p className="text-neutral-400 mb-8 max-w-lg mx-auto">
                    Get early access to Telos. Free during beta, no credit card required.
                </p>

                <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-3 justify-center items-center max-w-md mx-auto w-full">
                    <div className="relative w-full">
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                            required
                            disabled={status === "loading" || status === "success"}
                            className="w-full px-4 py-3 bg-neutral-900 border border-neutral-700 rounded-md focus:outline-none focus:border-terminal-green focus:ring-1 focus:ring-terminal-green text-white placeholder:text-neutral-600 transition-all disabled:opacity-50"
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
                                Get Early Access <ChevronRight className="w-4 h-4" />
                            </>
                        )}
                    </button>
                </form>

                {status === "error" && (
                    <div className="text-xs text-red-500 mt-4 font-mono bg-red-950/30 px-3 py-2 rounded border border-red-900/50 inline-block">
                        Error: {errorMsg || "Connection failed. Check your network."}
                    </div>
                )}

                <p className="text-xs text-neutral-600 mt-6">
                    We'll email you when it's ready. No spam, just product updates.
                </p>
            </div>
        </section>
    );
}

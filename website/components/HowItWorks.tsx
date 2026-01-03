"use client";

import { Download, Eye, MessageCircle, ShieldCheck, Lock, Database } from "lucide-react";
import { motion } from "framer-motion";

export function HowItWorks() {
    const steps = [
        {
            step: "1",
            title: "Install in 30 Seconds",
            description: "That's it. Works on Windows and macOS.",
            icon: Download
        },
        {
            step: "2",
            title: "It Watches Silently",
            description: "Telos runs in the background, watching what you work on. You'll barely know it's there.",
            icon: Eye
        },
        {
            step: "3",
            title: "Ask Questions Anytime",
            description: "\"What did I work on yesterday?\" Get instant, accurate answers about your work history.",
            icon: MessageCircle
        }
    ];

    const privacyFeatures = [
        {
            icon: ShieldCheck,
            title: "Data Deleted Instantly",
            description: "Activity data is processed and immediately removed. Never stored permanently."
        },
        {
            icon: Lock,
            title: "Data Never Leaves Your Device",
            description: "Everything is stored locally in SQLite. No cloud sync, no data harvesting."
        },
        {
            icon: Database,
            title: "You Own Your Data",
            description: "Export anytime. Delete anytime. Full control, always."
        }
    ];

    const testimonials = [
        {
            quote: "Finally, I can answer 'what did I do this week?' without guessing. Game changer for my weekly reports.",
            author: "Remote Developer",
            role: "Beta Tester"
        },
        {
            quote: "The AI chat is surprisingly accurate. Asked it when I finished a feature and it knew exactly.",
            author: "Freelance Designer",
            role: "Beta Tester"
        },
        {
            quote: "Love that it runs in the terminal. No Electron bloat, no tabs to keep open. Just works.",
            author: "Startup Founder",
            role: "Beta Tester"
        }
    ];

    return (
        <section className="py-20 px-4">
            <div className="max-w-5xl mx-auto">
                {/* How It Works */}
                <div className="mb-24">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold mb-4">How It Works</h2>
                        <p className="text-neutral-400">From install to insight in under a minute.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        {steps.map((item, index) => (
                            <div key={index} className="relative text-center group">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-xl bg-terminal-green/10 border border-terminal-green/20 flex items-center justify-center group-hover:bg-terminal-green/20 transition-colors">
                                    <item.icon className="w-7 h-7 text-terminal-green" />
                                </div>
                                <div className="absolute -top-2 -left-2 w-7 h-7 rounded-full bg-terminal-green text-black text-sm font-bold flex items-center justify-center md:static md:mx-auto md:mb-2 md:-mt-10 md:relative">
                                    {item.step}
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                                <p className="text-neutral-400 text-sm leading-relaxed">{item.description}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Privacy Section */}
                <div className="mb-24">
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold mb-4">Your Privacy is <span className="text-terminal-green">Non-Negotiable</span></h2>
                        <p className="text-neutral-400 max-w-xl mx-auto">
                            We built Telos for people who care about their data. That means keeping everything local and in your control.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {privacyFeatures.map((feature, index) => (
                            <div key={index} className="p-6 rounded-xl bg-neutral-900/50 border border-neutral-800 hover:border-terminal-green/30 transition-colors">
                                <feature.icon className="w-8 h-8 text-terminal-green mb-4" />
                                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                                <p className="text-neutral-400 text-sm">{feature.description}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Social Proof */}
                <div>
                    <div className="text-center mb-12">
                        <h2 className="text-3xl font-bold mb-4">What Beta Testers Say</h2>
                        <p className="text-neutral-400">Real feedback from people using Telos daily.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {testimonials.map((item, index) => (
                            <div key={index} className="p-6 rounded-xl bg-neutral-900/30 border border-neutral-800">
                                <p className="text-neutral-300 text-sm mb-4 leading-relaxed italic">"{item.quote}"</p>
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-terminal-green/30 to-blue-500/30 flex items-center justify-center text-white font-bold text-sm">
                                        {item.author.charAt(0)}
                                    </div>
                                    <div>
                                        <p className="text-white text-sm font-medium">{item.author}</p>
                                        <p className="text-neutral-500 text-xs">{item.role}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

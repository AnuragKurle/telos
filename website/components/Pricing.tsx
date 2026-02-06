"use client";

import { motion } from "framer-motion";
import { Check, Zap } from "lucide-react";

const trialFeatures = [
  "All features included",
  "AI-powered time tracking",
  "Daily email summaries",
  "AI chat with your data",
  "MCP server integration",
  "No credit card required",
];

const proFeatures = [
  "Everything in trial, forever",
  "Unlimited history retention",
  "Data export (CSV & JSON)",
  "Priority support",
  "No upgrade prompts",
  "Support indie development",
];

export function Pricing() {
  return (
    <section className="py-24 px-4 relative">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Simple, honest pricing
          </h2>
          <p className="text-neutral-400 text-lg max-w-2xl mx-auto">
            One plan. All features. No surprises.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {/* Free Trial */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            viewport={{ once: true }}
            className="border border-terminal-border rounded-xl p-8 bg-neutral-950/50"
          >
            <div className="mb-6">
              <h3 className="text-xl font-bold text-white mb-2">Free Trial</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-white">$0</span>
                <span className="text-neutral-500">/ 7 days</span>
              </div>
              <p className="text-neutral-400 text-sm mt-2">
                Try everything, no strings attached.
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              {trialFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-neutral-300">
                  <Check className="w-4 h-4 text-terminal-green flex-shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>

            <a
              href="#waitlist"
              className="block w-full text-center py-3 px-4 rounded-lg border border-terminal-border text-white font-medium hover:bg-neutral-800 transition-colors"
            >
              Start free trial
            </a>
          </motion.div>

          {/* Pro */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            viewport={{ once: true }}
            className="border border-terminal-green/30 rounded-xl p-8 bg-terminal-green/5 relative"
          >
            <div className="absolute -top-3 left-6">
              <span className="bg-terminal-green text-black text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                <Zap className="w-3 h-3" />
                RECOMMENDED
              </span>
            </div>

            <div className="mb-6">
              <h3 className="text-xl font-bold text-white mb-2">Telos Pro</h3>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-bold text-white">$3</span>
                <span className="text-neutral-500">/ month</span>
              </div>
              <p className="text-neutral-400 text-sm mt-2">
                Everything you need to understand your time.
              </p>
            </div>

            <ul className="space-y-3 mb-8">
              {proFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-neutral-300">
                  <Check className="w-4 h-4 text-terminal-green flex-shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>

            <a
              href="#waitlist"
              className="block w-full text-center py-3 px-4 rounded-lg bg-terminal-green text-black font-bold hover:bg-terminal-green/90 transition-colors"
            >
              Get started
            </a>
          </motion.div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          viewport={{ once: true }}
          className="text-center text-neutral-500 text-sm mt-8"
        >
          Cancel anytime. Your data stays on your machine — always.
        </motion.p>
      </div>
    </section>
  );
}

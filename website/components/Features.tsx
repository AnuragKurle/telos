import { FeatureCard } from "./FeatureCard";
import { Clock, Brain, Zap, Mail, Shield, MessageSquare } from "lucide-react";

export function Features() {
  const features = [
    {
      title: "Automatic Time Tracking",
      description: "See exactly what you worked on without logging anything manually. Fully automatic, zero effort.",
      icon: Clock
    },
    {
      title: "AI-Powered Insights",
      description: "Ask \"What did I do at 3pm?\" and get real answers. Natural language queries into your work history.",
      icon: Brain
    },
    {
      title: "Runs Silently",
      description: "Lightweight terminal app that runs in the background. Install once, works forever. No browser tabs to keep open.",
      icon: Zap
    },
    {
      title: "Daily Email Reports",
      description: "Wake up to a productivity summary in your inbox. Time breakdowns, patterns, and insights—automatically.",
      icon: Mail
    },
    {
      title: "100% Private",
      description: "Your work history lives only on your machine. Zero cloud uploads, zero data collection.",
      icon: Shield
    },
    {
      title: "Chat With Your Day",
      description: "\"Did I finish the API refactor?\" \"How much time on meetings?\" Ask anything about your work in plain English.",
      icon: MessageSquare
    }
  ];

  return (
    <section className="py-20 px-4 bg-neutral-950/50 border-y border-neutral-900">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">What You Get</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto">
            Simple, automatic time tracking that actually helps you understand where your time goes.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <FeatureCard key={index} {...feature} />
          ))}
        </div>
      </div>
    </section>
  );
}

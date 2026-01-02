import { FeatureCard } from "./FeatureCard";
import { Lock, Target, MessageSquare, ShieldAlert, Terminal, Zap } from "lucide-react";

export function Features() {
  const features = [
    {
      title: "Reality Logs",
      description: "One click to see the truth. Instantly visualize where your time slipped away versus where you thought it went.",
      icon: Target
    },
    {
      title: "Intention Alignment",
      description: "Define your goals for the session. Telos quietly measures your adherence and alerts you when you drift.",
      icon: ShieldAlert
    },
    {
      title: "Zero Overhead",
      description: "Lives in your terminal. No heavy Electron apps, no lag. Designed to be invisible until you need it.",
      icon: Terminal
    },
    {
      title: "The Guardian",
      description: "An active agent that fights for your focus. Connects with your calendar to protect your scheduled deep work blocks.",
      icon: Zap
    },
    {
      title: "Privacy First",
      description: "Your data lives locally on SQLite. AI reasoning happens on-demand via secure cloud inference, but memory is local.",
      icon: Lock
    },
    {
      title: "Chat Assistant",
      description: "Conversational interface to your work history. 'What was I doing at 10 AM?' 'Did I finish the deployment setup?'",
      icon: MessageSquare
    }
  ];

  return (
    <section className="py-20 px-4 bg-neutral-950/50 border-y border-neutral-900">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold mb-4">Fight the Slip</h2>
          <p className="text-neutral-400 max-w-2xl mx-auto">
            Algorithms are designed to steal your attention. Telos is designed to steal it back.
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

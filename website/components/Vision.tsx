import { CheckCircle2, Circle, Clock, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

export function Vision() {
  const roadmap = [
    {
      phase: "Phase 1",
      status: "current",
      title: "The Observer",
      description: "Passive logging and reporting. It watches your activity and provides retroactive insights on where your time went versus your intentions.",
      date: "Available Now"
    },
    {
      phase: "Phase 2",
      status: "planned",
      title: "The Guardian",
      description: "Active intervention. Google Calendar integration to understand your schedule. Real-time nudges when your screen activity contradicts your set intentions.",
      date: "Next Release"
    },
    {
      phase: "Phase 3",
      status: "planned",
      title: "The Sovereign",
      description: "Complete autonomy. Options for fully local AI processing. Cross-platform agents that work in unison to protect your digital life.",
      date: "Future"
    }
  ];

  return (
    <section className="py-20 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-16">
          <h2 className="text-3xl font-bold mb-4">Evolution of Assistance</h2>
          <p className="text-neutral-400">
            We are building an agent that works for you, not an algorithm that works on you.
          </p>
        </div>

        <div className="relative border-l border-neutral-800 ml-3 md:ml-6 space-y-12 pb-12">
          {roadmap.map((item, index) => (
            <div key={index} className="relative pl-8 md:pl-12 group">
              {/* Timeline Dot */}
              <div className={cn(
                "absolute -left-[5px] top-1 w-2.5 h-2.5 rounded-full border-2 bg-terminal-black transition-colors duration-300",
                item.status === "completed" ? "border-terminal-green bg-terminal-green" :
                item.status === "current" ? "border-terminal-green bg-terminal-green animate-pulse" :
                "border-neutral-700 group-hover:border-neutral-500"
              )} />
              
              <div className="flex flex-col sm:flex-row sm:items-baseline gap-2 mb-2">
                <span className={cn(
                  "font-mono text-sm font-bold uppercase tracking-wider",
                  item.status === "completed" ? "text-terminal-green" :
                  item.status === "current" ? "text-terminal-green" :
                  "text-neutral-500"
                )}>
                  {item.phase}
                </span>
                <span className="text-xs text-neutral-600 font-mono hidden sm:inline-block">/</span>
                <span className="text-xs text-neutral-600 font-mono">{item.date}</span>
              </div>

              <h3 className="text-xl font-bold text-white mb-2 group-hover:text-terminal-green transition-colors">
                {item.title}
              </h3>
              
              <p className="text-neutral-400 leading-relaxed max-w-2xl">
                {item.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

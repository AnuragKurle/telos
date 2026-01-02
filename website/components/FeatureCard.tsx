import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface FeatureCardProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  className?: string;
}

export function FeatureCard({ title, description, icon: Icon, className }: FeatureCardProps) {
  return (
    <div className={cn(
      "group p-6 border border-terminal-border rounded-md bg-neutral-900/30 hover:bg-neutral-900/60 transition-colors duration-300",
      className
    )}>
      <div className="flex items-center gap-3 mb-3">
        {Icon && <Icon className="w-5 h-5 text-terminal-green group-hover:text-terminal-amber transition-colors" />}
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <p className="text-neutral-400 text-sm leading-relaxed">
        {description}
      </p>
    </div>
  );
}


import * as React from "react";
import { cn } from "@/lib/utils";
import { Flame, Zap, DollarSign, Sparkles, Star } from "lucide-react";

interface SmartLabelProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant: "hot" | "urgent" | "high-value" | "new" | "priority";
  children: React.ReactNode;
}

const SmartLabel = React.forwardRef<HTMLSpanElement, SmartLabelProps>(
  ({ className, variant, children, ...props }, ref) => {
    const variantClasses = {
      hot: "smart-label-hot animate-pulse-glow",
      urgent: "smart-label-urgent",
      "high-value": "smart-label-high-value",
      new: "smart-label bg-blue-500/20 text-blue-400 border border-blue-500/30",
      priority: "smart-label bg-purple-500/20 text-purple-400 border border-purple-500/30",
    };

    const icons = {
      hot: Flame,
      urgent: Zap,
      "high-value": DollarSign,
      new: Sparkles,
      priority: Star,
    };

    const Icon = icons[variant];

    return (
      <span
        ref={ref}
        className={cn("smart-label", variantClasses[variant], className)}
        {...props}
      >
        <Icon className="w-3 h-3 mr-1 shrink-0" />
        <span className="truncate">{children}</span>
      </span>
    );
  }
);

SmartLabel.displayName = "SmartLabel";

export { SmartLabel };
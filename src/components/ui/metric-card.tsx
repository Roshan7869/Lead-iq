import * as React from "react";
import { cn } from "@/lib/utils";
import { Text } from "@/components/ui/text";
import type { LucideProps } from "lucide-react";

interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  icon?: React.ComponentType<LucideProps>;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  accent?: "primary" | "success" | "warning" | "error" | "info" | "accent";
  size?: "sm" | "md" | "lg";
}

const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(
  ({ className, label, value, icon: Icon, trend, accent = "primary", size = "md", ...props }, ref) => {
    const sizeClasses = {
      sm: "p-3",
      md: "p-4",
      lg: "p-6",
    };

    const accentClasses = {
      primary: "text-primary",
      success: "text-success",
      warning: "text-warning",
      error: "text-destructive",
      info: "text-info",
      accent: "text-accent",
    };

    return (
      <div
        ref={ref}
        className={cn(
          "glass-panel glass-panel-hover interactive-scale animate-slide-up",
          sizeClasses[size],
          className
        )}
        {...props}
      >
        <div className="flex items-center gap-2 mb-2">
          {Icon && <Icon className={cn("h-4 w-4", accentClasses[accent])} />}
          <Text variant="caption" className="font-medium">
            {label}
          </Text>
        </div>
        
        <div className="flex items-end justify-between">
          <Text 
            variant={size === "lg" ? "h2" : size === "md" ? "h3" : "h4"} 
            className={cn("font-mono", accentClasses[accent])}
          >
            {value}
          </Text>
          
          {trend && (
            <div className={cn(
              "flex items-center gap-1 text-xs font-medium",
              trend.isPositive ? "text-success" : "text-destructive"
            )}>
              <span>{trend.isPositive ? "↗" : "↘"}</span>
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
      </div>
    );
  }
);

MetricCard.displayName = "MetricCard";

export { MetricCard };
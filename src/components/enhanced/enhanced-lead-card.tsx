import { Lead, PRIORITY_ICON, SOURCE_CONFIG } from '@/types/lead';
import { useLeads } from '@/hooks/use-leads';
import { Text } from '@/components/ui/text';
import { SmartLabel } from '@/components/ui/smart-label';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  Flame, 
  Sun, 
  Snowflake, 
  Share2, 
  Linkedin, 
  Twitter, 
  Zap, 
  Cpu, 
  User,
  Lightbulb,
  Handshake,
  Target
} from 'lucide-react';
import * as LucideIcons from 'lucide-react';

interface EnhancedLeadCardProps {
  lead: Lead;
  compact?: boolean;
  showActions?: boolean;
}

const getLucideIcon = (name: string) => {
  const Icon = (LucideIcons as any)[name];
  return Icon ? <Icon className="w-4 h-4" /> : null;
};

export function EnhancedLeadCard({ lead, compact = false, showActions = true }: EnhancedLeadCardProps) {
  const { setSelectedLead } = useLeads();

  const getSmartLabels = () => {
    const labels = [];
    if (lead.intentScore >= 8) labels.push({ variant: "hot" as const, text: "Hot Lead" });
    if (lead.priority === 'hot') labels.push({ variant: "urgent" as const, text: "Urgent" });
    if (lead.estimatedValue >= 100000) labels.push({ variant: "high-value" as const, text: "High Value" });
    if (lead.stage === 'detected') labels.push({ variant: "new" as const, text: "New" });
    return labels;
  };

  const smartLabels = getSmartLabels();

  return (
    <div
      onClick={() => setSelectedLead(lead)}
      className={cn(
        "glass-panel glass-panel-hover interactive-scale cursor-pointer group",
        "transition-all duration-300 ease-out overflow-hidden max-w-full",
        compact ? "p-3" : "p-4"
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-secondary/50 flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-muted-foreground" />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Text variant="h6" className="truncate group-hover:text-primary transition-colors">
              {lead.name}
            </Text>
            <span className="text-muted-foreground flex-shrink-0">
              {getLucideIcon(PRIORITY_ICON[lead.priority])}
            </span>
          </div>
          
          <Text variant="xs" color="muted" className="truncate block">
            {lead.title}
          </Text>
          <Text variant="xs" color="muted" className="truncate block opacity-70">
            {lead.company}
          </Text>
        </div>
        
        <div className="flex flex-col items-end gap-0.5 flex-shrink-0 ml-1">
          <Text variant="mono" color="primary" className="font-bold text-sm">
            {lead.intentScore}
          </Text>
          <Text variant="xs" className="text-[10px] uppercase font-semibold opacity-50 tracking-wider">INTENT</Text>
        </div>
      </div>

      {/* Smart Labels */}
      {smartLabels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {smartLabels.map((label, index) => (
            <SmartLabel key={index} variant={label.variant} className="text-[10px] px-1.5 py-0.5">
              {label.text}
            </SmartLabel>
          ))}
        </div>
      )}

      {/* Signal */}
      {!compact && (
        <div className="mb-3">
          <Text variant="small" className="italic text-muted-foreground line-clamp-2 leading-relaxed text-[11px]">
            "{lead.signal}"
          </Text>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1 min-w-0">
          <div className="flex items-center gap-1 bg-secondary/30 px-2 py-0.5 rounded border border-border/30 max-w-full">
            <span className="text-muted-foreground flex-shrink-0">
              {getLucideIcon(SOURCE_CONFIG[lead.source].icon)}
            </span>
            <span className="text-[10px] font-medium truncate">
              {SOURCE_CONFIG[lead.source].label}
            </span>
          </div>
          <Badge variant="outline" className="text-[10px] px-1 py-0 h-auto">
            {lead.fundingStage}
          </Badge>
        </div>
        
        <div className="flex-shrink-0">
          <Text variant="mono" className="text-xs font-bold text-success">
            ₹{(lead.estimatedValue / 1000).toFixed(0)}K
          </Text>
        </div>
      </div>

      {/* Recommended Action */}
      {showActions && (
        <div className="mt-3 pt-3 border-t border-border/20">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-1 text-muted-foreground">
              <Lightbulb className="w-3 h-3" />
              <Text variant="xs" className="text-[10px] font-medium">RECAP:</Text>
            </div>
            <div className="flex items-center gap-1">
              {lead.outreachStrategy === 'warm_intro' ? (
                <>
                  <Handshake className="w-3 h-3 text-primary" />
                  <Text variant="xs" className="text-[10px] font-bold text-primary">WARM INTRO</Text>
                </>
              ) : (
                <>
                  <Target className="w-3 h-3 text-secondary-foreground" />
                  <Text variant="xs" className="text-[10px] font-bold text-secondary-foreground">DIRECT PITCH</Text>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
"use client";

import { Lead, PRIORITY_ICON, SOURCE_CONFIG } from '@/types/lead';
import { useLeads } from '@/hooks/use-leads';

interface LeadCardProps {
  lead: Lead;
  compact?: boolean;
}

export function LeadCard({ lead, compact }: LeadCardProps) {
  const { setSelectedLead } = useLeads();

  return (
    <button
      onClick={() => setSelectedLead(lead)}
      className="w-full text-left glass-panel p-4 hover:border-primary/30 transition-all duration-200 group cursor-pointer"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl">{lead.avatar}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-foreground truncate">{lead.name}</span>
            <span className="text-sm">{PRIORITY_ICON[lead.priority]}</span>
          </div>
          <p className="text-sm text-muted-foreground truncate">{lead.title} · {lead.company}</p>
          {!compact && (
            <p className="text-xs text-muted-foreground mt-1.5 line-clamp-2 italic">{lead.signal}</p>
          )}
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <span className="text-xs bg-secondary px-2 py-0.5 rounded-full text-secondary-foreground">
              {SOURCE_CONFIG[lead.source].icon} {SOURCE_CONFIG[lead.source].label}
            </span>
            <span className="text-xs font-mono text-primary">
              Intent: {lead.intentScore}
            </span>
            <span className="text-xs font-mono text-muted-foreground ml-auto">
              ₹{(lead.estimatedValue / 1000).toFixed(0)}K
            </span>
          </div>
        </div>
      </div>
    </button>
  );
}

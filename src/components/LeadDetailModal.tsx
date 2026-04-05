"use client";

import { useLeads } from '@/hooks/use-leads';
import { STAGE_CONFIG, SOURCE_CONFIG, PRIORITY_ICON } from '@/types/lead';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, Mail, Linkedin } from 'lucide-react';

export function LeadDetailModal() {
  const { selectedLead, setSelectedLead } = useLeads();
  if (!selectedLead) return null;

  const lead = selectedLead;
  const stageInfo = STAGE_CONFIG[lead.stage];
  const sourceInfo = SOURCE_CONFIG[lead.source];

  return (
    <Dialog open={!!selectedLead} onOpenChange={() => setSelectedLead(null)}>
      <DialogContent className="sm:max-w-lg bg-card border-border">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            <span className="text-3xl">{lead.avatar}</span>
            <div>
              <div className="flex items-center gap-2">
                <span>{lead.name}</span>
                <span>{PRIORITY_ICON[lead.priority]}</span>
              </div>
              <p className="text-sm text-muted-foreground font-normal">{lead.title} · {lead.company}</p>
            </div>
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={stageInfo.color}>{stageInfo.label}</Badge>
            <Badge variant="outline">{sourceInfo.icon} {sourceInfo.label}</Badge>
            <Badge variant="outline">{lead.fundingStage}</Badge>
            <Badge variant="outline">
              {lead.outreachStrategy === 'warm_intro' ? '🤝 Warm Intro' : '🎯 Direct Pitch'}
            </Badge>
          </div>

          {/* Signal */}
          <div className="glass-panel p-3">
            <p className="text-xs text-muted-foreground mb-1 font-medium">Detected Signal</p>
            <p className="text-sm italic text-foreground">{lead.signal}</p>
          </div>

          {/* Scores */}
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Intent', value: lead.intentScore, color: 'text-primary' },
              { label: 'Founder', value: lead.founderScore, color: 'text-accent' },
              { label: 'Network', value: lead.networkScore, color: 'text-info' },
            ].map((s) => (
              <div key={s.label} className="glass-panel p-3 text-center">
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className={`text-xl font-bold font-mono ${s.color}`}>{s.value}</p>
              </div>
            ))}
          </div>

          {/* Value & Contact */}
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Estimated Value</p>
              <p className="text-lg font-bold font-mono text-primary">₹{lead.estimatedValue.toLocaleString('en-IN')}</p>
            </div>
            <div className="flex gap-2">
              <a href={`mailto:${lead.email}`} className="glass-panel p-2 hover:border-primary/40 transition-colors">
                <Mail className="h-4 w-4 text-muted-foreground" />
              </a>
              <a href={lead.linkedinUrl} target="_blank" rel="noreferrer" className="glass-panel p-2 hover:border-primary/40 transition-colors">
                <Linkedin className="h-4 w-4 text-muted-foreground" />
              </a>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

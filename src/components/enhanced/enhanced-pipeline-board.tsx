import { useLeads } from '@/hooks/use-leads';
import { STAGE_CONFIG, LeadStage } from '@/types/lead';
import { EnhancedLeadCard } from './enhanced-lead-card';
import { Text } from '@/components/ui/text';
import { Badge } from '@/components/ui/badge';

const STAGES: LeadStage[] = ['detected', 'qualified', 'contacted', 'meeting', 'closed'];

export function EnhancedPipelineBoard() {
  const { leads } = useLeads();

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-6 min-h-[70vh]">
      {STAGES.map((stage, stageIndex) => {
        const stageLeads = leads.filter(l => l.stage === stage);
        const config = STAGE_CONFIG[stage];
        const totalValue = stageLeads.reduce((sum, lead) => sum + lead.estimatedValue, 0);
        
        return (
          <div 
            key={stage} 
            className="space-y-4 animate-slide-up"
            style={{ animationDelay: `${stageIndex * 100}ms` }}
          >
            {/* Column Header */}
            <div className="glass-panel p-4">
              <div className="flex items-center justify-between mb-2">
                <Text variant="h6" className={config.color}>
                  {config.label}
                </Text>
                <Badge variant="secondary" className="text-xs">
                  {stageLeads.length}
                </Badge>
              </div>
              
              <div className="flex items-center justify-between">
                <Text variant="xs" color="muted">
                  Total Value
                </Text>
                <Text variant="mono" className="text-xs font-bold text-success">
                  ₹{(totalValue / 1000).toFixed(0)}K
                </Text>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-2 h-1 bg-secondary rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all duration-1000 ${config.color.replace('text-', 'bg-')}`}
                  style={{ 
                    width: `${Math.min((stageLeads.length / Math.max(...STAGES.map(s => leads.filter(l => l.stage === s).length))) * 100, 100)}%`,
                    animationDelay: `${stageIndex * 200}ms`
                  }}
                />
              </div>
            </div>

            {/* Lead Cards */}
            <div className="space-y-3">
              {stageLeads.map((lead, leadIndex) => (
                <div
                  key={lead.id}
                  className="animate-slide-in-right"
                  style={{ animationDelay: `${(stageIndex * 100) + (leadIndex * 50)}ms` }}
                >
                  <EnhancedLeadCard 
                    lead={lead} 
                    compact={stage === 'closed'}
                    showActions={stage === 'detected' || stage === 'qualified'}
                  />
                </div>
              ))}
              
              {stageLeads.length === 0 && (
                <div className="glass-panel p-6 text-center">
                  <Text variant="small" color="muted">
                    No leads in this stage
                  </Text>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
import { DashboardLayout } from '@/components/DashboardLayout';
import { useLeads } from '@/hooks/use-leads';
import { STAGE_CONFIG, LeadStage } from '@/types/lead';
import { IndianRupee, TrendingUp, Server, Sparkles } from 'lucide-react';

const STAGES: LeadStage[] = ['detected', 'qualified', 'contacted', 'meeting', 'closed'];

export default function ROITrackerPage() {
  const { leads } = useLeads();

  const revenue = leads.filter(l => l.stage === 'closed').reduce((s, l) => s + l.estimatedValue, 0);
  const pipeline = leads.filter(l => l.stage !== 'closed').reduce((s, l) => s + l.estimatedValue, 0);
  const cost = 1600;
  const net = revenue - cost;
  const multiplier = revenue > 0 ? (revenue / cost).toFixed(0) : '0';

  const funnelData = STAGES.map((stage) => ({
    stage,
    label: STAGE_CONFIG[stage].label,
    count: leads.filter(l => l.stage === stage).length,
    color: STAGE_CONFIG[stage].color,
  }));

  const maxCount = Math.max(...funnelData.map(d => d.count), 1);

  const metricCards = [
    { label: 'Total Revenue', value: `₹${revenue.toLocaleString('en-IN')}`, icon: IndianRupee, accent: 'text-success' },
    { label: 'Pipeline Value', value: `₹${pipeline.toLocaleString('en-IN')}`, icon: TrendingUp, accent: 'text-accent' },
    { label: 'Server Cost', value: `₹${cost.toLocaleString('en-IN')}/mo`, icon: Server, accent: 'text-warning' },
    { label: 'Net ROI', value: `${multiplier}x`, icon: Sparkles, accent: 'text-primary' },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">ROI Tracker</h1>
          <p className="text-sm text-muted-foreground mt-1">Revenue metrics and conversion funnel</p>
        </div>

        {/* Metric Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {metricCards.map((card) => (
            <div key={card.label} className="glass-panel p-5 animate-slide-up">
              <div className="flex items-center gap-2 mb-2">
                <card.icon className={`h-5 w-5 ${card.accent}`} />
                <span className="text-xs text-muted-foreground font-medium">{card.label}</span>
              </div>
              <p className={`text-2xl font-bold font-mono ${card.accent}`}>{card.value}</p>
            </div>
          ))}
        </div>

        {/* Conversion Funnel */}
        <div className="glass-panel p-6">
          <h2 className="text-lg font-semibold text-foreground mb-6">Conversion Funnel</h2>
          <div className="space-y-4">
            {funnelData.map((d) => {
              const pct = ((d.count / leads.length) * 100).toFixed(0);
              return (
                <div key={d.stage} className="flex items-center gap-4">
                  <span className={`text-sm font-medium w-24 ${d.color}`}>{d.label}</span>
                  <div className="flex-1 h-8 bg-secondary/50 rounded-lg overflow-hidden">
                    <div
                      className="h-full bg-primary/60 rounded-lg transition-all duration-500 flex items-center px-3"
                      style={{ width: `${Math.max((d.count / maxCount) * 100, 8)}%` }}
                    >
                      <span className="text-xs font-mono text-primary-foreground font-bold">{d.count}</span>
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground font-mono w-10 text-right">{pct}%</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Default pricing */}
        <div className="glass-panel p-5 border-primary/20">
          <p className="text-sm text-muted-foreground">
            Default deal value: <span className="text-primary font-bold font-mono">₹50,000</span> (~$600) per closed project.
            Range varies ₹30K–₹200K based on project scope.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}

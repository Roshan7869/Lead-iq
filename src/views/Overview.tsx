"use client";

import dynamic from 'next/dynamic';
import { useLeads } from '@/hooks/use-leads';
import { STAGE_CONFIG, LeadStage } from '@/types/lead';
import { DashboardLayout } from '@/components/DashboardLayout';
import { Text } from '@/components/ui/text';

const EnhancedStatsCards = dynamic(
  () => import('@/components/enhanced/enhanced-stats-cards').then((m) => ({ default: m.EnhancedStatsCards })),
  { ssr: false, loading: () => <div className="grid grid-cols-2 md:grid-cols-3 gap-4">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-24 glass-panel animate-pulse rounded-xl" />)}</div> }
);

const EnhancedLeadCard = dynamic(
  () => import('@/components/enhanced/enhanced-lead-card').then((m) => ({ default: m.EnhancedLeadCard })),
  { ssr: false, loading: () => <div className="h-32 glass-panel animate-pulse rounded-xl" /> }
);

const LeadDetailModal = dynamic(
  () => import('@/components/LeadDetailModal').then((m) => ({ default: m.LeadDetailModal })),
  { ssr: false }
);

const STAGES: LeadStage[] = ['detected', 'qualified', 'contacted', 'meeting', 'closed'];

export default function OverviewPage() {
  const { leads } = useLeads();
  const recentLeads = [...leads].sort((a, b) => new Date(b.lastActivity).getTime() - new Date(a.lastActivity).getTime()).slice(0, 4);

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="animate-slide-up">
          <Text variant="h1" className="text-gradient">
            Overview
          </Text>
          <Text variant="body" color="muted" className="mt-2">
            🧠 AI-powered lead intelligence dashboard
          </Text>
        </div>

        <EnhancedStatsCards />

        {/* Recent Activity */}
        <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
          <div className="flex items-center gap-2 mb-4">
            <Text variant="h3">⚡ Recent Activity</Text>
            <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            {recentLeads.map((lead, index) => (
              <div
                key={lead.id}
                className="animate-slide-in-right"
                style={{ animationDelay: `${300 + (index * 100)}ms` }}
              >
                <EnhancedLeadCard lead={lead} compact />
              </div>
            ))}
          </div>
        </div>

        {/* Mini Pipeline */}
        <div className="animate-slide-up" style={{ animationDelay: '400ms' }}>
          <Text variant="h3" className="mb-4">📊 Pipeline Snapshot</Text>
          <div className="grid grid-cols-5 gap-3">
            {STAGES.map((stage, index) => {
              const count = leads.filter(l => l.stage === stage).length;
              const config = STAGE_CONFIG[stage];
              return (
                <div 
                  key={stage} 
                  className="glass-panel glass-panel-hover interactive-scale p-4 text-center animate-slide-up"
                  style={{ animationDelay: `${500 + (index * 100)}ms` }}
                >
                  <Text variant="h2" className={`font-mono ${config.color}`}>
                    {count}
                  </Text>
                  <Text variant="caption" className="mt-1">
                    {config.label}
                  </Text>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <LeadDetailModal />
    </DashboardLayout>
  );
}

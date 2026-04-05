"use client";

import dynamic from 'next/dynamic';
import { DashboardLayout } from '@/components/DashboardLayout';
import { useLeads } from '@/hooks/use-leads';
import { SOURCE_CONFIG, LeadSource } from '@/types/lead';
import { Text } from '@/components/ui/text';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';

const EnhancedLeadCard = dynamic(
  () => import('@/components/enhanced/enhanced-lead-card').then((m) => ({ default: m.EnhancedLeadCard })),
  { ssr: false, loading: () => <div className="h-32 glass-panel animate-pulse rounded-xl" /> }
);

const LeadDetailModal = dynamic(
  () => import('@/components/LeadDetailModal').then((m) => ({ default: m.LeadDetailModal })),
  { ssr: false }
);

const SOURCES: LeadSource[] = ['reddit', 'linkedin', 'x', 'yc', 'indie_hackers'];

export default function DemandMinerPage() {
  const { leads } = useLeads();
  const [activeSource, setActiveSource] = useState<LeadSource | 'all'>('all');

  const filtered = activeSource === 'all' ? leads : leads.filter(l => l.source === activeSource);
  const detected = filtered.filter(l => l.stage === 'detected');
  const others = filtered.filter(l => l.stage !== 'detected');

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="animate-slide-up">
          <Text variant="h1" className="text-gradient">
            ⛏️ Demand Miner
          </Text>
          <Text variant="body" color="muted" className="mt-2">
            🤖 AI-powered signal detection across all platforms
          </Text>
        </div>

        {/* Source filters */}
        <div className="flex flex-wrap gap-2 animate-slide-up" style={{ animationDelay: '100ms' }}>
          <button
            onClick={() => setActiveSource('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 interactive-scale ${
              activeSource === 'all' 
                ? 'bg-primary text-primary-foreground glow-primary' 
                : 'glass-panel glass-panel-hover text-muted-foreground hover:text-foreground'
            }`}
          >
            🌐 All 
            <Badge variant="secondary" className="ml-2">
              {leads.length}
            </Badge>
          </button>
          {SOURCES.map((source, index) => {
            const count = leads.filter(l => l.source === source).length;
            const config = SOURCE_CONFIG[source];
            return (
              <button
                key={source}
                onClick={() => setActiveSource(source)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 interactive-scale animate-slide-in-right ${
                  activeSource === source 
                    ? 'bg-primary text-primary-foreground glow-primary' 
                    : 'glass-panel glass-panel-hover text-muted-foreground hover:text-foreground'
                }`}
                style={{ animationDelay: `${150 + (index * 50)}ms` }}
              >
                {config.icon} {config.label}
                <Badge variant="secondary" className="ml-2">
                  {count}
                </Badge>
              </button>
            );
          })}
        </div>

        {/* New signals */}
        {detected.length > 0 && (
          <div className="animate-slide-up" style={{ animationDelay: '200ms' }}>
            <div className="flex items-center gap-2 mb-4">
              <Text variant="h3">🆕 New Signals</Text>
              <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
              <Badge variant="outline" className="bg-success/20 text-success border-success/30">
                {detected.length} Fresh
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-3">
              {detected.map((lead, index) => (
                <div
                  key={lead.id}
                  className="animate-slide-in-right"
                  style={{ animationDelay: `${300 + (index * 100)}ms` }}
                >
                  <EnhancedLeadCard lead={lead} />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Processed */}
        {others.length > 0 && (
          <div className="animate-slide-up" style={{ animationDelay: '300ms' }}>
            <div className="flex items-center gap-2 mb-4">
              <Text variant="h3">🔄 Already In Pipeline</Text>
              <Badge variant="outline" className="bg-info/20 text-info border-info/30">
                {others.length} Processing
              </Badge>
            </div>
            <div className="grid md:grid-cols-2 gap-3">
              {others.map((lead, index) => (
                <div
                  key={lead.id}
                  className="animate-slide-in-right"
                  style={{ animationDelay: `${400 + (index * 50)}ms` }}
                >
                  <EnhancedLeadCard lead={lead} compact />
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Empty State */}
        {filtered.length === 0 && (
          <div className="glass-panel p-12 text-center animate-slide-up">
            <Text variant="h4" color="muted" className="mb-2">
              🔍 No signals detected
            </Text>
            <Text variant="body" color="muted">
              AI is actively monitoring for new opportunities
            </Text>
          </div>
        )}
      </div>

      <LeadDetailModal />
    </DashboardLayout>
  );
}

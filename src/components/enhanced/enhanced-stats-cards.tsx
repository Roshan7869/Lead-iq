"use client";

import { useLeads } from '@/hooks/use-leads';
import { MetricCard } from '@/components/ui/metric-card';
import { Users, UserCheck, Send, Handshake, IndianRupee, TrendingUp } from 'lucide-react';

export function EnhancedStatsCards() {
  const { leads } = useLeads();

  const total = leads.length;
  const qualified = leads.filter(l => l.stage !== 'detected').length;
  const contacted = leads.filter(l => ['contacted', 'meeting', 'closed'].includes(l.stage)).length;
  const closed = leads.filter(l => l.stage === 'closed').length;
  const revenue = leads.filter(l => l.stage === 'closed').reduce((s, l) => s + l.estimatedValue, 0);
  const pipeline = leads.filter(l => l.stage !== 'closed').reduce((s, l) => s + l.estimatedValue, 0);

  const metrics = [
    { 
      label: 'Total Leads', 
      value: total, 
      icon: Users, 
      accent: 'info' as const,
      trend: { value: 12, isPositive: true }
    },
    { 
      label: 'Qualified', 
      value: qualified, 
      icon: UserCheck, 
      accent: 'warning' as const,
      trend: { value: 8, isPositive: true }
    },
    { 
      label: 'Contacted', 
      value: contacted, 
      icon: Send, 
      accent: 'accent' as const,
      trend: { value: 15, isPositive: true }
    },
    { 
      label: 'Closed', 
      value: closed, 
      icon: Handshake, 
      accent: 'success' as const,
      trend: { value: 25, isPositive: true }
    },
    { 
      label: 'Revenue', 
      value: `₹${(revenue / 1000).toFixed(0)}K`, 
      icon: IndianRupee, 
      accent: 'primary' as const,
      trend: { value: 45, isPositive: true }
    },
    { 
      label: 'Pipeline', 
      value: `₹${(pipeline / 1000).toFixed(0)}K`, 
      icon: TrendingUp, 
      accent: 'accent' as const,
      trend: { value: 18, isPositive: true }
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {metrics.map((metric, index) => (
        <MetricCard
          key={metric.label}
          label={metric.label}
          value={metric.value}
          icon={metric.icon}
          accent={metric.accent}
          trend={metric.trend}
          style={{ animationDelay: `${index * 100}ms` }}
        />
      ))}
    </div>
  );
}
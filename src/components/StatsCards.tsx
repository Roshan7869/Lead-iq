"use client";

import { useLeads } from '@/hooks/use-leads';
import { Users, UserCheck, Send, Handshake, IndianRupee, TrendingUp } from 'lucide-react';

export function StatsCards() {
  const { leads } = useLeads();

  const total = leads.length;
  const qualified = leads.filter(l => l.stage !== 'detected').length;
  const contacted = leads.filter(l => ['contacted', 'meeting', 'closed'].includes(l.stage)).length;
  const closed = leads.filter(l => l.stage === 'closed').length;
  const revenue = leads.filter(l => l.stage === 'closed').reduce((s, l) => s + l.estimatedValue, 0);
  const pipeline = leads.filter(l => l.stage !== 'closed').reduce((s, l) => s + l.estimatedValue, 0);

  const cards = [
    { label: 'Total Leads', value: total, icon: Users, accent: 'text-info' },
    { label: 'Qualified', value: qualified, icon: UserCheck, accent: 'text-warning' },
    { label: 'Contacted', value: contacted, icon: Send, accent: 'text-accent' },
    { label: 'Closed', value: closed, icon: Handshake, accent: 'text-success' },
    { label: 'Revenue', value: `₹${(revenue / 1000).toFixed(0)}K`, icon: IndianRupee, accent: 'text-primary' },
    { label: 'Pipeline', value: `₹${(pipeline / 1000).toFixed(0)}K`, icon: TrendingUp, accent: 'text-accent' },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="glass-panel p-4 animate-slide-up">
          <div className="flex items-center gap-2 mb-2">
            <card.icon className={`h-4 w-4 ${card.accent}`} />
            <span className="text-xs text-muted-foreground font-medium">{card.label}</span>
          </div>
          <p className={`text-2xl font-bold font-mono ${card.accent}`}>{card.value}</p>
        </div>
      ))}
    </div>
  );
}

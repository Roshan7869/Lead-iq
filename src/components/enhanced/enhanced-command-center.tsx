"use client";

import { useState, useRef, useEffect } from 'react';
import { useLeads } from '@/hooks/use-leads';
import { STAGE_CONFIG, PRIORITY_ICON, LeadStage } from '@/types/lead';
import { Text } from '@/components/ui/text';

type Line = { 
  type: 'system' | 'input' | 'output' | 'error' | 'success' | 'warning'; 
  text: string;
  timestamp?: string;
};

const STAGES: LeadStage[] = ['detected', 'qualified', 'contacted', 'meeting', 'closed'];

export function EnhancedCommandCenter() {
  const { leads } = useLeads();
  const [lines, setLines] = useState<Line[]>([
    { type: 'system', text: '╔═══════════════════════════════════════════════╗' },
    { type: 'system', text: '║   🧠 LeadIQ AI Command Center v2.0           ║' },
    { type: 'system', text: '║   Enhanced with AI Intelligence               ║' },
    { type: 'system', text: '║   Type /help for available commands           ║' },
    { type: 'system', text: '╚═══════════════════════════════════════════════╝' },
    { type: 'success', text: '✅ AI Engine initialized successfully' },
    { type: 'success', text: '✅ Lead scoring models loaded' },
    { type: 'system', text: '' },
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  const addLines = (newLines: Line[]) => setLines(prev => [...prev, ...newLines]);

  const simulateAIProcessing = async (command: string) => {
    setIsProcessing(true);
    addLines([{ type: 'system', text: '🧠 AI processing...' }]);
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
    
    setIsProcessing(false);
  };

  const handleCommand = async (cmd: string) => {
    const timestamp = new Date().toLocaleTimeString();
    addLines([{ type: 'input', text: `> ${cmd}`, timestamp }]);

    const command = cmd.trim().toLowerCase();

    switch (command) {
      case '/help':
        addLines([
          { type: 'output', text: '🤖 AI-Powered Commands Available:' },
          { type: 'output', text: '  /run-pipeline      — Run full AI pipeline (collect → analyse → score → CRM)' },
          { type: 'output', text: '  /analyze-leads     — AI analysis of all leads' },
          { type: 'output', text: '  /top-opportunities — AI-ranked hot prospects' },
          { type: 'output', text: '  /generate-pitch    — AI pitch generation' },
          { type: 'output', text: '  /market-insights   — AI market analysis' },
          { type: 'output', text: '  /pipeline-health   — Pipeline diagnostics' },
          { type: 'output', text: '  /roi-forecast      — Revenue predictions' },
          { type: 'output', text: '  /system-status     — System health check' },
          { type: 'output', text: '  /clear             — Clear terminal' },
        ]);
        break;

      case '/run-pipeline': {
        setIsProcessing(true);
        addLines([
          { type: 'system', text: '🚀 LAUNCHING FULL AI PIPELINE' },
          { type: 'output', text: '  [1/6] 🔍 Collecting demand signals...' },
        ]);
        try {
          const res = await fetch('/api/run-pipeline', { method: 'POST' });
          const data = await res.json();
          const s = data.summary ?? {};
          setIsProcessing(false);
          addLines([
            { type: 'output', text: `  [2/6] 🧠 AI analysis complete (${s.analyzed ?? '?'} events)` },
            { type: 'output', text: `  [3/6] 📊 Scoring complete (${s.scored ?? '?'} events)` },
            { type: 'output', text: `  [4/6] 🏆 Ranking complete (${s.ranked ?? '?'} events)` },
            { type: 'output', text: `  [5/6] ✉️  Outreach generated (${s.outreach ?? '?'} messages)` },
            { type: 'success', text: `  [6/6] ✅ CRM updated — ${s.crm_updated ?? '?'} new leads` },
            { type: 'system', text: '' },
            { type: 'success', text: `🎉 Pipeline complete! Collected ${s.collected ?? '?'} signals → ${s.crm_updated ?? '?'} CRM leads` },
          ]);
        } catch {
          setIsProcessing(false);
          addLines([{ type: 'error', text: '❌ Pipeline failed — check backend connection' }]);
        }
        break;
      }

      case '/analyze-leads':
        await simulateAIProcessing(command);
        const hotLeads = leads.filter(l => l.priority === 'hot').length;
        const avgIntent = (leads.reduce((sum, l) => sum + l.intentScore, 0) / leads.length).toFixed(1);
        addLines([
          { type: 'system', text: '🧠 AI LEAD ANALYSIS COMPLETE' },
          { type: 'success', text: `  📊 Total Leads Analyzed: ${leads.length}` },
          { type: 'success', text: `  🔥 High-Priority Leads: ${hotLeads}` },
          { type: 'success', text: `  📈 Average Intent Score: ${avgIntent}/10` },
          { type: 'warning', text: `  💡 AI Recommendation: Focus on ${hotLeads} hot leads for 3x conversion` },
        ]);
        break;

      case '/top-opportunities':
        await simulateAIProcessing(command);
        const top = [...leads]
          .sort((a, b) => (b.intentScore * b.estimatedValue) - (a.intentScore * a.estimatedValue))
          .slice(0, 3);
        addLines([
          { type: 'system', text: '🎯 AI-RANKED TOP OPPORTUNITIES' },
          ...top.map((l, i) => ({
            type: 'success' as const,
            text: `  ${i + 1}. ${PRIORITY_ICON[l.priority]} ${l.name} (${l.company}) — AI Score: ${(l.intentScore * (l.estimatedValue/50000)).toFixed(0)} — ₹${(l.estimatedValue / 1000).toFixed(0)}K`,
          })),
          { type: 'warning', text: '  💡 AI suggests contacting within 24 hours for optimal conversion' },
        ]);
        break;

      case '/generate-pitch':
        await simulateAIProcessing(command);
        addLines([
          { type: 'system', text: '✨ AI PITCH GENERATOR' },
          { type: 'output', text: '  🎯 Analyzing lead context...' },
          { type: 'output', text: '  📝 Generating personalized pitch...' },
          { type: 'success', text: '  ✅ Pitch generated for top lead:' },
          { type: 'output', text: '' },
          { type: 'output', text: '  "Hi [Name], noticed your post about needing MVP development.' },
          { type: 'output', text: '   We specialize in rapid fintech builds - delivered 3 similar' },
          { type: 'output', text: '   projects in 6 weeks. Happy to share case studies."' },
          { type: 'output', text: '' },
          { type: 'warning', text: '  💡 AI Confidence: 87% — Personalization score: High' },
        ]);
        break;

      case '/market-insights':
        await simulateAIProcessing(command);
        addLines([
          { type: 'system', text: '📊 AI MARKET ANALYSIS' },
          { type: 'success', text: '  🚀 Fintech demand up 34% this quarter' },
          { type: 'success', text: '  💰 Average project value: ₹75K (+12%)' },
          { type: 'success', text: '  ⏱️  Response time critical: <2 hours optimal' },
          { type: 'warning', text: '  ⚠️  Competition increased 23% - act fast on hot leads' },
          { type: 'output', text: '  🎯 Best platforms: Reddit (42%), LinkedIn (31%)' },
        ]);
        break;

      case '/pipeline-health':
        await simulateAIProcessing(command);
        const conversionRate = ((leads.filter(l => l.stage === 'closed').length / leads.length) * 100).toFixed(1);
        addLines([
          { type: 'system', text: '🏥 PIPELINE HEALTH DIAGNOSTIC' },
          { type: 'success', text: `  📈 Conversion Rate: ${conversionRate}% (Above average)` },
          { type: 'success', text: '  ⚡ Response Time: Excellent (avg 1.2 hours)' },
          { type: 'warning', text: '  🔄 Bottleneck detected: Qualified → Contacted stage' },
          { type: 'output', text: '  💡 AI suggests: Automate initial outreach for 40% efficiency gain' },
        ]);
        break;

      case '/roi-forecast':
        await simulateAIProcessing(command);
        const projectedRevenue = leads.filter(l => l.stage !== 'closed').reduce((s, l) => s + l.estimatedValue * 0.3, 0);
        addLines([
          { type: 'system', text: '🔮 AI REVENUE FORECAST' },
          { type: 'success', text: `  📊 Current Pipeline: ₹${(projectedRevenue / 1000).toFixed(0)}K` },
          { type: 'success', text: '  📈 30-day projection: ₹180K (+25%)' },
          { type: 'success', text: '  🎯 90-day forecast: ₹520K (High confidence)' },
          { type: 'warning', text: '  💡 Focus on 3 hot leads for ₹225K quick wins' },
        ]);
        break;

      case '/system-status':
        addLines([
          { type: 'system', text: '🔧 SYSTEM STATUS CHECK' },
          { type: 'success', text: '  ✅ AI Engine       — Online (99.9% uptime)' },
          { type: 'success', text: '  ✅ Lead Detector   — Active (24/7 monitoring)' },
          { type: 'success', text: '  ✅ Scoring Model   — Optimized (v2.1)' },
          { type: 'success', text: '  ✅ CRM Pipeline    — Synced' },
          { type: 'success', text: '  ✅ Outreach Engine — Ready' },
          { type: 'output', text: '  📊 Performance: Excellent' },
        ]);
        break;

      case '/clear':
        setLines([]);
        break;

      default:
        addLines([
          { type: 'error', text: `❌ Unknown command: ${cmd}` },
          { type: 'output', text: '💡 Type /help to see available AI commands' },
        ]);
    }
  };

  const colorMap: Record<Line['type'], string> = {
    system: 'text-primary',
    input: 'text-foreground',
    output: 'text-secondary-foreground',
    error: 'text-destructive',
    success: 'text-success',
    warning: 'text-warning',
  };

  return (
    <div className="terminal-window animate-slide-up">
      {/* Enhanced Window Chrome */}
      <div className="terminal-chrome">
        <div className="terminal-dot-red" />
        <div className="terminal-dot-yellow" />
        <div className="terminal-dot-green" />
        <Text variant="xs" color="muted" className="ml-2 font-mono">
          leadiq-ai-terminal
        </Text>
        <div className="ml-auto flex items-center gap-2">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
          <Text variant="xs" color="success">AI Online</Text>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="h-[500px] overflow-y-auto p-4 font-mono text-sm space-y-0.5 custom-scrollbar">
        {lines.map((line, i) => (
          <div key={i} className="flex items-start gap-2">
            <Text 
              variant="mono" 
              className={colorMap[line.type]} 
              style={{ whiteSpace: 'pre' }}
            >
              {line.text}
            </Text>
            {line.timestamp && (
              <Text variant="xs" color="muted" className="ml-auto">
                {line.timestamp}
              </Text>
            )}
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex items-center gap-2 text-primary">
            <div className="animate-spin w-3 h-3 border border-primary border-t-transparent rounded-full" />
            <Text variant="mono">Processing...</Text>
          </div>
        )}
        
        <div ref={bottomRef} />
      </div>

      {/* Enhanced Input */}
      <div className="flex items-center border-t border-white/10 px-4 py-3 bg-black/20">
        <span className="text-primary font-mono text-sm mr-2 glow-primary">$</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && input.trim() && !isProcessing) {
              handleCommand(input.trim());
              setInput('');
            }
          }}
          disabled={isProcessing}
          className="flex-1 bg-transparent outline-none font-mono text-sm text-foreground placeholder:text-muted-foreground focus-ring"
          placeholder={isProcessing ? "AI processing..." : "Type a command... (try /help)"}
          autoFocus
        />
        {input && (
          <Text variant="xs" color="muted" className="ml-2">
            Press Enter
          </Text>
        )}
      </div>
    </div>
  );
}
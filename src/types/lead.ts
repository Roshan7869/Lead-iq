export type LeadStage = 'detected' | 'qualified' | 'contacted' | 'meeting' | 'closed';
export type LeadSource = 'reddit' | 'linkedin' | 'x' | 'yc' | 'indie_hackers';
export type LeadPriority = 'hot' | 'warm' | 'cold';

export interface Lead {
  id: string;
  name: string;
  company: string;
  title: string;
  stage: LeadStage;
  source: LeadSource;
  priority: LeadPriority;
  intentScore: number;
  founderScore: number;
  fundingStage: string;
  networkScore: number;
  detectedAt: string;
  lastActivity: string;
  signal: string;
  estimatedValue: number;
  outreachStrategy: 'warm_intro' | 'direct_pitch';
  avatar: string;
  email: string;
  linkedinUrl: string;
}

export const STAGE_CONFIG: Record<LeadStage, { label: string; color: string }> = {
  detected: { label: 'Detected', color: 'text-info' },
  qualified: { label: 'Qualified', color: 'text-warning' },
  contacted: { label: 'Contacted', color: 'text-accent' },
  meeting: { label: 'Meeting', color: 'text-primary' },
  closed: { label: 'Closed', color: 'text-success' },
};

export const SOURCE_CONFIG: Record<LeadSource, { label: string; icon: string }> = {
  reddit: { label: 'Reddit', icon: 'Share2' },
  linkedin: { label: 'LinkedIn', icon: 'Linkedin' },
  x: { label: 'X / Twitter', icon: 'Twitter' },
  yc: { label: 'Y Combinator', icon: 'Zap' },
  indie_hackers: { label: 'Indie Hackers', icon: 'Cpu' },
};

export const PRIORITY_ICON: Record<LeadPriority, string> = {
  hot: 'Flame',
  warm: 'Sun',
  cold: 'Snowflake',
};

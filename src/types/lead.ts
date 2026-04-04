// ── Operation Modes ───────────────────────────────────────────────────────────

export type OperationMode = 'b2b_sales' | 'hiring' | 'job_search' | 'opportunity';

export const MODE_CONFIG: Record<OperationMode, { label: string; description: string; icon: string }> = {
  b2b_sales:   { label: 'B2B Sales',       description: 'Find companies with buying intent', icon: 'Target' },
  hiring:      { label: 'Talent Hunting',  description: 'Find fast-growing companies hiring', icon: 'Users' },
  job_search:  { label: 'Job Search',      description: 'Find open roles matching your skills', icon: 'Briefcase' },
  opportunity: { label: 'Market Scout',    description: 'Detect emerging market gaps', icon: 'Telescope' },
};

// ── Core Lead Types ───────────────────────────────────────────────────────────

export type LeadStage = 'detected' | 'qualified' | 'contacted' | 'meeting' | 'closed';
export type LeadSource = 'reddit' | 'linkedin' | 'x' | 'yc' | 'indie_hackers' | 'producthunt' | 'stackoverflow' | 'hn' | 'twitter' | 'github' | 'rss';
export type LeadPriority = 'hot' | 'warm' | 'cold';
export type ScoreBand = 'hot' | 'warm' | 'cool' | 'cold';
export type CompanySize = 'startup' | 'smb' | 'enterprise' | 'unknown';

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

/** Extended lead schema returned by the backend API */
export interface BackendLead {
  id: string;
  is_opportunity: boolean;
  confidence: number;
  intent: string;
  urgency: string;
  opportunity_score: number;
  icp_fit_score: number;
  final_score: number;
  priority: string;
  score_band: ScoreBand | null;
  company_name: string | null;
  company_size: CompanySize | null;
  industry: string | null;
  contact_name: string | null;
  contact_title: string | null;
  stage: string;
  notes: string | null;
  outreach_draft: string | null;
  created_at: string;
  updated_at: string;
}

/** PersonalizedLeadOut — from /api/profile/leads */
export interface PersonalizedLead extends BackendLead {
  personalized_score: number;
  temporal_decay: number;
  profile_fit: number;
  keyword_bonus: number;
  feedback_bonus: number;
  velocity_bonus: number;
}

// ── User Profile ──────────────────────────────────────────────────────────────

export interface UserProfile {
  mode: OperationMode;
  productDescription: string;
  targetCustomer: string;
  targetIndustries: string[];
  targetCompanySizes: string[];
  includeKeywords: string[];
  excludeKeywords: string[];
  hiringRoles: string[];
  skills: string[];
  minSalary: number;
  remoteOnly: boolean;
}

export const DEFAULT_PROFILE: UserProfile = {
  mode: 'b2b_sales',
  productDescription: '',
  targetCustomer: '',
  targetIndustries: [],
  targetCompanySizes: [],
  includeKeywords: [],
  excludeKeywords: [],
  hiringRoles: [],
  skills: [],
  minSalary: 0,
  remoteOnly: false,
};

// ── UI Config Maps ────────────────────────────────────────────────────────────

export const STAGE_CONFIG: Record<LeadStage, { label: string; color: string }> = {
  detected:  { label: 'Detected',  color: 'text-info' },
  qualified: { label: 'Qualified', color: 'text-warning' },
  contacted: { label: 'Contacted', color: 'text-accent' },
  meeting:   { label: 'Meeting',   color: 'text-primary' },
  closed:    { label: 'Closed',    color: 'text-success' },
};

export const SOURCE_CONFIG: Record<string, { label: string; icon: string }> = {
  reddit:       { label: 'Reddit',        icon: 'Share2' },
  linkedin:     { label: 'LinkedIn',      icon: 'Linkedin' },
  x:            { label: 'X / Twitter',   icon: 'Twitter' },
  twitter:      { label: 'X / Twitter',   icon: 'Twitter' },
  yc:           { label: 'Y Combinator',  icon: 'Zap' },
  indie_hackers:{ label: 'Indie Hackers', icon: 'Cpu' },
  producthunt:  { label: 'ProductHunt',   icon: 'Cat' },
  stackoverflow:{ label: 'Stack Overflow',icon: 'Code2' },
  hn:           { label: 'Hacker News',   icon: 'Flame' },
  github:       { label: 'GitHub',        icon: 'Github' },
  rss:          { label: 'RSS / Blog',    icon: 'Rss' },
};

export const PRIORITY_ICON: Record<LeadPriority, string> = {
  hot:  'Flame',
  warm: 'Sun',
  cold: 'Snowflake',
};

export const SCORE_BAND_CONFIG: Record<ScoreBand, { label: string; color: string }> = {
  hot:  { label: 'Hot',  color: 'text-red-500' },
  warm: { label: 'Warm', color: 'text-orange-400' },
  cool: { label: 'Cool', color: 'text-blue-400' },
  cold: { label: 'Cold', color: 'text-slate-400' },
};

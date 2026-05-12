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
export type LeadSource = 'reddit' | 'linkedin' | 'x' | 'yc' | 'indie_hackers'
  | 'producthunt' | 'stackoverflow' | 'hn' | 'twitter' | 'github' | 'rss'
  | 'github_issues' | 'telegram' | 'naukri' | 'internshala' | 'indeed'
  | 'linkedin_jobs' | 'shine' | 'cutshort' | 'foundit' | 'freejobalert'
  | 'freshersworld' | 'hirect' | 'hirist' | 'iimjobs' | 'instahyre'
  | 'monster' | 'naukrigulf' | 'sarkari_result' | 'timesjobs' | 'weekday'
  | 'employment_news' | 'angellist' | 'crunchbase';
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

export const SOURCE_CONFIG: Record<string, { label: string; icon: string; category?: string }> = {
  reddit:        { label: 'Reddit',        icon: 'Share2',       category: 'community' },
  linkedin:      { label: 'LinkedIn',      icon: 'Linkedin',     category: 'community' },
  x:             { label: 'X / Twitter',   icon: 'Twitter',      category: 'community' },
  twitter:       { label: 'X / Twitter',   icon: 'Twitter',      category: 'community' },
  yc:            { label: 'Y Combinator',  icon: 'Zap',          category: 'community' },
  indie_hackers: { label: 'Indie Hackers', icon: 'Cpu',          category: 'community' },
  producthunt:   { label: 'ProductHunt',   icon: 'Cat',          category: 'community' },
  stackoverflow: { label: 'Stack Overflow',icon: 'Code2',        category: 'community' },
  hn:            { label: 'Hacker News',   icon: 'Flame',        category: 'community' },
  github:        { label: 'GitHub',        icon: 'Github',       category: 'community' },
  rss:           { label: 'RSS / Blog',    icon: 'Rss',          category: 'community' },
  github_issues: { label: 'GitHub Issues', icon: 'GitPullRequest', category: 'community' },
  telegram:      { label: 'Telegram',      icon: 'Send',         category: 'community' },
  indeed:        { label: 'Indeed',        icon: 'Briefcase',    category: 'jobs' },
  naukri:        { label: 'Naukri',        icon: 'Briefcase',    category: 'jobs' },
  internshala:   { label: 'Internshala',   icon: 'GraduationCap',category: 'jobs' },
  linkedin_jobs: { label: 'LinkedIn Jobs', icon: 'Linkedin',     category: 'jobs' },
  shine:         { label: 'Shine',         icon: 'Briefcase',    category: 'jobs' },
  cutshort:      { label: 'Cutshort',      icon: 'Zap',          category: 'jobs' },
  foundit:       { label: 'Foundit',       icon: 'Search',       category: 'jobs' },
  hirect:        { label: 'Hirect',        icon: 'MessageCircle',category: 'jobs' },
  instahyre:     { label: 'Instahyre',     icon: 'Star',         category: 'jobs' },
  monster:       { label: 'Monster',       icon: 'Briefcase',    category: 'jobs' },
  timesjobs:     { label: 'TimesJobs',     icon: 'Clock',        category: 'jobs' },
  weekday:       { label: 'Weekday',       icon: 'Calendar',     category: 'jobs' },
  freejobalert:  { label: 'FreeJobAlert',  icon: 'Bell',         category: 'jobs' },
  freshersworld: { label: 'Freshersworld', icon: 'Users',        category: 'jobs' },
  hirist:        { label: 'Hirist',        icon: 'Code2',        category: 'jobs' },
  iimjobs:       { label: 'IIMJobs',       icon: 'Award',        category: 'jobs' },
  naukrigulf:    { label: 'NaukriGulf',    icon: 'Globe',        category: 'jobs' },
  sarkari_result:{ label: 'Sarkari Result',icon: 'FileText',     category: 'jobs' },
  employment_news:{ label: 'Employment News', icon: 'Newspaper',  category: 'jobs' },
  angellist:     { label: 'AngelList',     icon: 'Angel',        category: 'funding' },
  crunchbase:    { label: 'Crunchbase',    icon: 'Database',     category: 'funding' },
};

import { Flame, Sun, Snowflake, type LucideIcon } from 'lucide-react';

export const PRIORITY_ICON: Record<LeadPriority, LucideIcon> = {
  hot:  Flame,
  warm: Sun,
  cold: Snowflake,
};

export const SCORE_BAND_CONFIG: Record<ScoreBand, { label: string; color: string }> = {
  hot:  { label: 'Hot',  color: 'text-red-500' },
  warm: { label: 'Warm', color: 'text-orange-400' },
  cool: { label: 'Cool', color: 'text-blue-400' },
  cold: { label: 'Cold', color: 'text-slate-400' },
};

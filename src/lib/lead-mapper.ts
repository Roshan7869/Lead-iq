/**
 * lib/lead-mapper.ts — Converts backend Lead data to frontend Lead type.
 *
 * Maps BackendLead (from /api/leads) to Lead (used by UI components).
 * Falls back to demo data if backend is unavailable.
 */

import { Lead } from '@/types/lead';
import { BackendLead, PersonalizedLead } from '@/types/lead';

/**
 * Map BackendLead to frontend Lead type for UI components.
 */
export function mapBackendLeadToLead(backendLead: BackendLead | PersonalizedLead): Lead {
  // Determine priority based on score band or backend priority
  let priority: 'hot' | 'warm' | 'cold' = 'cold';
  if (backendLead.score_band === 'hot' || backendLead.priority === 'high') {
    priority = 'hot';
  } else if (backendLead.score_band === 'warm' || backendLead.priority === 'medium') {
    priority = 'warm';
  }

  // Map stage
  const stage = backendLead.stage as 'detected' | 'qualified' | 'contacted' | 'meeting' | 'closed';

  // Determine source from source_actor or fallback
  let source: 'reddit' | 'linkedin' | 'x' | 'yc' | 'indie_hackers' | 'producthunt' | 'stackoverflow' | 'hn' | 'twitter' | 'github' | 'rss' = 'reddit';
  const sourceActor = (backendLead as any).source_actor?.toLowerCase() || '';
  if (sourceActor.includes('reddit')) source = 'reddit';
  else if (sourceActor.includes('linkedin')) source = 'linkedin';
  else if (sourceActor.includes('twitter') || sourceActor.includes('x')) source = 'x';
  else if (sourceActor.includes('yc') || sourceActor.includes('y-combinator')) source = 'yc';
  else if (sourceActor.includes('indie')) source = 'indie_hackers';
  else if (sourceActor.includes('producthunt')) source = 'producthunt';
  else if (sourceActor.includes('stackoverflow')) source = 'stackoverflow';
  else if (sourceActor.includes('hn') || sourceActor.includes('hacker')) source = 'hn';
  else if (sourceActor.includes('github')) source = 'github';
  else if (sourceActor.includes('rss')) source = 'rss';

  // Generate estimated value from opportunity score
  const estimatedValue = Math.round(backendLead.opportunity_score * 1000);

  // Fallback name from contact_name or company_name
  const name = backendLead.contact_name || backendLead.company_name || 'Unknown';
  const company = backendLead.company_name || 'Unknown';
  const title = backendLead.contact_title || 'Unknown';

  // Map outreach strategy based on priority
  const outreachStrategy: 'warm_intro' | 'direct_pitch' = priority === 'warm' ? 'warm_intro' : 'direct_pitch';

  return {
    id: backendLead.id,
    name,
    company,
    title,
    stage,
    source,
    priority,
    intentScore: Math.min(10, Math.round(backendLead.confidence * 10 + (backendLead.opportunity_score / 20))),
    founderScore: Math.min(10, Math.round((backendLead.confidence + backendLead.icp_fit_score) / 2)),
    fundingStage: 'Pre-Seed',
    networkScore: Math.min(10, Math.round(backendLead.icp_fit_score)),
    detectedAt: backendLead.created_at,
    lastActivity: backendLead.updated_at,
    signal: backendLead.outreach_draft || `Opportunity: ${backendLead.intent}`,
    estimatedValue,
    outreachStrategy,
    avatar: getAvatarFromName(name),
    email: '',
    linkedinUrl: '',
  };
}

/**
 * Map a list of backend leads to frontend Lead type.
 */
export function mapBackendLeadsToLeads(backendLeads: (BackendLead | PersonalizedLead)[]): Lead[] {
  return backendLeads.map(mapBackendLeadToLead);
}

/**
 * Get a person emoji avatar based on name.
 */
function getAvatarFromName(name: string): string {
  const names = name.split(' ');
  if (names.length === 0) return '👤';

  const firstChar = names[0].charAt(0).toUpperCase();
  const lastChar = names[names.length - 1].charAt(0).toUpperCase();

  const emojis = [
    '👨‍💼', '👩‍💼', '👨‍💻', '👩‍💻', '👨‍🎓', '👩‍🎓', '👨‍🔬', '👩‍🔬',
    '👨‍🎨', '👩‍🎨', '👨‍⚕️', '👩‍⚕️', '👨‍✈️', '👩‍✈️', '👨‍🚀', '👩‍🚀',
    '🧑‍💼', '🧑‍💻', '🧑‍🎓', '🧑‍🔧', '🧑‍🎨', '🧑‍⚕️', '🧑‍🔬', '🧑‍🎤'
  ];

  // Simple hash to pick an emoji
  const hash = firstChar.charCodeAt(0) + lastChar.charCodeAt(0);
  return emojis[hash % emojis.length];
}

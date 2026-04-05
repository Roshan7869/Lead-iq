"use client";

import { useState, KeyboardEvent } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import {
  Target, Users, Briefcase, Telescope,
  ChevronRight, ChevronLeft, Check, Plus, X, Loader2,
} from 'lucide-react';
import { useProfile } from '@/hooks/use-profile';
import { OperationMode, MODE_CONFIG, UserProfile, DEFAULT_PROFILE } from '@/types/lead';
import { cn } from '@/lib/utils';

// ── Types ─────────────────────────────────────────────────────────────────────

interface WizardProps {
  open: boolean;
  onClose: () => void;
}

type WizardStep = 'mode' | 'target' | 'keywords' | 'details' | 'confirm';
const STEPS: WizardStep[] = ['mode', 'target', 'keywords', 'details', 'confirm'];

// ── Icon map ──────────────────────────────────────────────────────────────────

const MODE_ICONS: Record<OperationMode, React.ComponentType<{ className?: string }>> = {
  b2b_sales:   Target,
  hiring:      Users,
  job_search:  Briefcase,
  opportunity: Telescope,
};

const MODE_COLORS: Record<OperationMode, string> = {
  b2b_sales:   'from-violet-600 to-purple-700',
  hiring:      'from-blue-600 to-cyan-600',
  job_search:  'from-emerald-600 to-teal-600',
  opportunity: 'from-orange-600 to-amber-600',
};

// ── Industry options ──────────────────────────────────────────────────────────

const INDUSTRIES = [
  'saas', 'devtools', 'fintech', 'ai', 'healthtech',
  'ecommerce', 'marketplace', 'edtech', 'climate', 'enterprise',
];

const COMPANY_SIZES = [
  { value: 'startup',   label: 'Startup (1–50)' },
  { value: 'smb',       label: 'SMB (51–500)' },
  { value: 'enterprise',label: 'Enterprise (500+)' },
];

// ── TagInput helper ───────────────────────────────────────────────────────────

function TagInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
}) {
  const [input, setInput] = useState('');

  function add() {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
    }
    setInput('');
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      add();
    }
    if (e.key === 'Backspace' && !input && value.length) {
      onChange(value.slice(0, -1));
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          placeholder={placeholder}
          className="flex-1"
        />
        <Button type="button" variant="outline" size="sm" onClick={add}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1 pr-1">
              {tag}
              <button
                type="button"
                onClick={() => onChange(value.filter((t) => t !== tag))}
                className="hover:text-destructive transition-colors"
                aria-label={`Remove ${tag}`}
              >
                <X className="w-3 h-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Multi-select pills ────────────────────────────────────────────────────────

function PillSelect({
  options,
  value,
  onChange,
  label,
}: {
  options: { value: string; label: string }[];
  value: string[];
  onChange: (v: string[]) => void;
  label?: string;
}) {
  function toggle(v: string) {
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  }

  return (
    <div className="space-y-1.5">
      {label && <p className="text-sm text-muted-foreground">{label}</p>}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => toggle(opt.value)}
            className={cn(
              'px-3 py-1.5 rounded-full text-sm font-medium transition-all border',
              value.includes(opt.value)
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border text-muted-foreground hover:border-primary hover:text-foreground',
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── Main wizard ───────────────────────────────────────────────────────────────

export function ProfileSetupWizard({ open, onClose }: WizardProps) {
  const { saveProfile } = useProfile();
  const [step, setStep]   = useState<WizardStep>('mode');
  const [saving, setSaving] = useState(false);
  const [draft, setDraft] = useState<UserProfile>({ ...DEFAULT_PROFILE });

  const stepIdx     = STEPS.indexOf(step);
  const progressPct = ((stepIdx + 1) / STEPS.length) * 100;

  function update(patch: Partial<UserProfile>) {
    setDraft((prev) => ({ ...prev, ...patch }));
  }

  function next() {
    if (stepIdx < STEPS.length - 1) setStep(STEPS[stepIdx + 1]);
  }

  function back() {
    if (stepIdx > 0) setStep(STEPS[stepIdx - 1]);
  }

  async function finish() {
    setSaving(true);
    try {
      await saveProfile(draft);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  // ── Step: Mode selection ───────────────────────────────────────────────────

  function StepMode() {
    const modes = Object.entries(MODE_CONFIG) as [OperationMode, typeof MODE_CONFIG[OperationMode]][];
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">What are you mining for?</h2>
          <p className="text-muted-foreground text-sm mt-1">
            LeadIQ adapts its AI, sources, and scoring to your exact goal.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {modes.map(([mode, config]) => {
            const Icon    = MODE_ICONS[mode];
            const active  = draft.mode === mode;
            return (
              <button
                key={mode}
                type="button"
                onClick={() => update({ mode })}
                className={cn(
                  'group relative rounded-xl p-4 text-left transition-all border-2',
                  active
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/40 bg-card',
                )}
              >
                <div className={cn('w-10 h-10 rounded-lg bg-gradient-to-br flex items-center justify-center mb-3', MODE_COLORS[mode])}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <p className="font-semibold text-sm">{config.label}</p>
                <p className="text-xs text-muted-foreground mt-0.5 leading-snug">{config.description}</p>
                {active && (
                  <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-primary flex items-center justify-center">
                    <Check className="w-3 h-3 text-primary-foreground" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  }

  // ── Step: Targeting ────────────────────────────────────────────────────────

  function StepTarget() {
    const showProductFields = draft.mode === 'b2b_sales';
    const showSkillFields   = draft.mode === 'job_search' || draft.mode === 'hiring';

    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">Define your target</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Who are you looking for? More detail = better personalization.
          </p>
        </div>

        {showProductFields && (
          <div className="space-y-1.5">
            <Label>What does your product do?</Label>
            <Textarea
              rows={2}
              placeholder="We build AI-powered analytics for SaaS companies…"
              value={draft.productDescription}
              onChange={(e) => update({ productDescription: e.target.value })}
            />
          </div>
        )}

        <div className="space-y-1.5">
          <Label>
            {draft.mode === 'job_search'
              ? 'Describe your ideal role / company'
              : 'Who is your ideal target?'}
          </Label>
          <Textarea
            rows={2}
            placeholder={
              draft.mode === 'job_search'
                ? 'Series A startup, remote-friendly, mission-driven…'
                : 'Founders and CTOs at early-stage B2B SaaS companies…'
            }
            value={draft.targetCustomer}
            onChange={(e) => update({ targetCustomer: e.target.value })}
          />
        </div>

        <PillSelect
          options={INDUSTRIES.map((i) => ({ value: i, label: i.toUpperCase() }))}
          value={draft.targetIndustries}
          onChange={(v) => update({ targetIndustries: v })}
          label="Target industries (select all that apply)"
        />

        <PillSelect
          options={COMPANY_SIZES}
          value={draft.targetCompanySizes}
          onChange={(v) => update({ targetCompanySizes: v })}
          label="Company sizes"
        />
      </div>
    );
  }

  // ── Step: Keywords ─────────────────────────────────────────────────────────

  function StepKeywords() {
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">Signal keywords</h2>
          <p className="text-muted-foreground text-sm mt-1">
            Include boosts matches. Exclude hard-blocks them from results.
          </p>
        </div>

        <div className="space-y-1.5">
          <Label>Include keywords <span className="text-muted-foreground font-normal">(boost score)</span></Label>
          <TagInput
            value={draft.includeKeywords}
            onChange={(v) => update({ includeKeywords: v })}
            placeholder="e.g. frustrated, switching tool, looking for — press Enter"
          />
        </div>

        <div className="space-y-1.5">
          <Label>Exclude keywords <span className="text-muted-foreground font-normal">(hard block)</span></Label>
          <TagInput
            value={draft.excludeKeywords}
            onChange={(v) => update({ excludeKeywords: v })}
            placeholder="e.g. student, academic, homework — press Enter"
          />
        </div>
      </div>
    );
  }

  // ── Step: Mode-specific details ────────────────────────────────────────────

  function StepDetails() {
    if (draft.mode === 'hiring') {
      return (
        <div className="space-y-5">
          <div>
            <h2 className="text-xl font-bold">Roles you&apos;re filling</h2>
            <p className="text-muted-foreground text-sm mt-1">
              LeadIQ will prioritise companies hiring for these positions.
            </p>
          </div>
          <TagInput
            value={draft.hiringRoles}
            onChange={(v) => update({ hiringRoles: v })}
            placeholder="e.g. Senior Backend Engineer, ML Engineer — press Enter"
          />
        </div>
      );
    }

    if (draft.mode === 'job_search') {
      return (
        <div className="space-y-5">
          <div>
            <h2 className="text-xl font-bold">Your skills &amp; preferences</h2>
            <p className="text-muted-foreground text-sm mt-1">
              Matches open roles that fit your background.
            </p>
          </div>

          <div className="space-y-1.5">
            <Label>Your skills</Label>
            <TagInput
              value={draft.skills}
              onChange={(v) => update({ skills: v })}
              placeholder="e.g. Python, TypeScript, React — press Enter"
            />
          </div>

          <div className="space-y-1.5">
            <Label>Minimum salary (USD/year)</Label>
            <Input
              type="number"
              min={0}
              step={10000}
              value={draft.minSalary || ''}
              onChange={(e) => update({ minSalary: Number(e.target.value) })}
              placeholder="120000"
            />
          </div>

          <div className="flex items-center gap-3">
            <Switch
              checked={draft.remoteOnly}
              onCheckedChange={(v) => update({ remoteOnly: v })}
              id="remote"
            />
            <Label htmlFor="remote">Remote only</Label>
          </div>
        </div>
      );
    }

    // b2b_sales + opportunity — no extra step needed
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">Almost there!</h2>
          <p className="text-muted-foreground text-sm mt-1">
            No extra configuration needed for{' '}
            <strong>{MODE_CONFIG[draft.mode].label}</strong> mode.
            Click <em>Next</em> to review and launch.
          </p>
        </div>
        <div className={cn('rounded-xl p-5 bg-gradient-to-br', MODE_COLORS[draft.mode])}>
          <div className="flex items-center gap-3 text-white">
            {(() => { const Icon = MODE_ICONS[draft.mode]; return <Icon className="w-6 h-6" />; })()}
            <div>
              <p className="font-bold">{MODE_CONFIG[draft.mode].label}</p>
              <p className="text-sm opacity-80">{MODE_CONFIG[draft.mode].description}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── Step: Confirm ──────────────────────────────────────────────────────────

  function StepConfirm() {
    const Icon = MODE_ICONS[draft.mode];
    return (
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-bold">Ready to launch 🚀</h2>
          <p className="text-muted-foreground text-sm mt-1">Review your profile before mining begins.</p>
        </div>

        <div className="rounded-xl border border-border bg-card/50 divide-y divide-border text-sm">
          <div className="flex items-center gap-3 p-4">
            <div className={cn('w-8 h-8 rounded-lg bg-gradient-to-br flex items-center justify-center shrink-0', MODE_COLORS[draft.mode])}>
              <Icon className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="font-semibold">{MODE_CONFIG[draft.mode].label}</p>
              <p className="text-xs text-muted-foreground">{MODE_CONFIG[draft.mode].description}</p>
            </div>
          </div>

          {draft.targetIndustries.length > 0 && (
            <div className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Industries</p>
              <div className="flex flex-wrap gap-1">
                {draft.targetIndustries.map((i) => (
                  <Badge key={i} variant="secondary">{i}</Badge>
                ))}
              </div>
            </div>
          )}

          {draft.includeKeywords.length > 0 && (
            <div className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Boost keywords</p>
              <div className="flex flex-wrap gap-1">
                {draft.includeKeywords.map((k) => (
                  <Badge key={k} className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">{k}</Badge>
                ))}
              </div>
            </div>
          )}

          {draft.excludeKeywords.length > 0 && (
            <div className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Block keywords</p>
              <div className="flex flex-wrap gap-1">
                {draft.excludeKeywords.map((k) => (
                  <Badge key={k} className="bg-red-500/20 text-red-400 border-red-500/30">{k}</Badge>
                ))}
              </div>
            </div>
          )}

          {draft.mode === 'job_search' && (draft.skills.length > 0 || draft.minSalary > 0) && (
            <div className="p-4 space-y-2">
              {draft.skills.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Skills</p>
                  <div className="flex flex-wrap gap-1">{draft.skills.map((s) => <Badge key={s} variant="outline">{s}</Badge>)}</div>
                </div>
              )}
              {draft.minSalary > 0 && (
                <p className="text-xs text-muted-foreground">Min salary: <span className="text-foreground font-medium">${draft.minSalary.toLocaleString()}/yr</span></p>
              )}
              {draft.remoteOnly && <p className="text-xs text-emerald-400">Remote only ✓</p>}
            </div>
          )}

          {draft.mode === 'hiring' && draft.hiringRoles.length > 0 && (
            <div className="p-4 space-y-1">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Roles hiring for</p>
              <div className="flex flex-wrap gap-1">
                {draft.hiringRoles.map((r) => <Badge key={r} variant="outline">{r}</Badge>)}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  const stepLabels: Record<WizardStep, string> = {
    mode:     'Mode',
    target:   'Target',
    keywords: 'Keywords',
    details:  'Details',
    confirm:  'Confirm',
  };

  return (
    <Dialog open={open} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] flex flex-col overflow-hidden p-0 gap-0">
        {/* Header */}
        <DialogHeader className="px-6 pt-6 pb-3 shrink-0">
          <div className="flex items-center justify-between mb-3">
            <DialogTitle className="text-base font-medium text-muted-foreground">
              Profile Setup — Step {stepIdx + 1} of {STEPS.length}
            </DialogTitle>
            <div className="flex gap-1">
              {STEPS.map((s, i) => (
                <div
                  key={s}
                  className={cn(
                    'h-1.5 rounded-full transition-all',
                    i <= stepIdx ? 'bg-primary' : 'bg-border',
                    i === stepIdx ? 'w-6' : 'w-2',
                  )}
                />
              ))}
            </div>
          </div>
          <Progress value={progressPct} className="h-1" />

          {/* Step breadcrumb */}
          <div className="flex gap-3 pt-1">
            {STEPS.map((s, i) => (
              <span
                key={s}
                className={cn(
                  'text-xs transition-colors',
                  i === stepIdx ? 'text-foreground font-medium' : 'text-muted-foreground',
                  i < stepIdx ? 'line-through opacity-50' : '',
                )}
              >
                {stepLabels[s]}
              </span>
            ))}
          </div>
        </DialogHeader>

        {/* Step content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {step === 'mode'     && <StepMode />}
          {step === 'target'   && <StepTarget />}
          {step === 'keywords' && <StepKeywords />}
          {step === 'details'  && <StepDetails />}
          {step === 'confirm'  && <StepConfirm />}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border shrink-0 flex items-center justify-between gap-3">
          <Button
            variant="ghost"
            onClick={stepIdx === 0 ? onClose : back}
            disabled={saving}
          >
            {stepIdx === 0 ? 'Skip for now' : <><ChevronLeft className="w-4 h-4 mr-1" /> Back</>}
          </Button>

          {step === 'confirm' ? (
            <Button onClick={finish} disabled={saving} className="gap-2">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              {saving ? 'Saving…' : 'Start Mining'}
            </Button>
          ) : (
            <Button onClick={next}>
              Next <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

"use client";

import {
  useState,
  useEffect,
  createContext,
  useContext,
  useCallback,
  ReactNode,
} from 'react';
import { UserProfile, OperationMode, DEFAULT_PROFILE } from '@/types/lead';

const PROFILE_STORAGE_KEY = 'leadiq:user_profile';
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

// ── Context ───────────────────────────────────────────────────────────────────

interface ProfileContextType {
  profile: UserProfile;
  isSetupComplete: boolean;
  isSaving: boolean;
  saveProfile: (updates: Partial<UserProfile>) => Promise<void>;
  setMode: (mode: OperationMode) => Promise<void>;
}

const ProfileContext = createContext<ProfileContextType | undefined>(undefined);

// ── Local persistence helpers ─────────────────────────────────────────────────

function loadFromStorage(): UserProfile {
  if (typeof window === 'undefined') return DEFAULT_PROFILE;
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
    if (raw) return { ...DEFAULT_PROFILE, ...JSON.parse(raw) };
  } catch {}
  return DEFAULT_PROFILE;
}

function saveToStorage(profile: UserProfile): void {
  try {
    localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(profile));
  } catch {}
}

// ── Backend sync (best-effort) ────────────────────────────────────────────────

async function syncToBackend(profile: UserProfile): Promise<void> {
  if (!API_BASE) return;
  const payload = {
    mode:                  profile.mode,
    product_description:   profile.productDescription,
    target_customer:       profile.targetCustomer,
    target_industries:     profile.targetIndustries,
    target_company_sizes:  profile.targetCompanySizes,
    include_keywords:      profile.includeKeywords,
    exclude_keywords:      profile.excludeKeywords,
    hiring_roles:          profile.hiringRoles,
    skills:                profile.skills,
    min_salary:            profile.minSalary,
    remote_only:           profile.remoteOnly,
  };

  // Import lazily to avoid circular deps (auth-client → use-profile)
  const { getAuthHeader } = await import('@/lib/auth-client');
  await fetch(`${API_BASE}/api/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(payload),
  });
}

async function loadFromBackend(): Promise<Partial<UserProfile> | null> {
  if (!API_BASE) return null;
  try {
    const resp = await fetch(`${API_BASE}/api/profile`);
    if (!resp.ok) return null;
    const data = await resp.json();
    // Map snake_case API → camelCase local
    return {
      mode:                data.mode               ?? DEFAULT_PROFILE.mode,
      productDescription:  data.product_description ?? '',
      targetCustomer:      data.target_customer      ?? '',
      targetIndustries:    data.target_industries    ?? [],
      targetCompanySizes:  data.target_company_sizes ?? [],
      includeKeywords:     data.include_keywords     ?? [],
      excludeKeywords:     data.exclude_keywords     ?? [],
      hiringRoles:         data.hiring_roles         ?? [],
      skills:              data.skills               ?? [],
      minSalary:           data.min_salary           ?? 0,
      remoteOnly:          data.remote_only          ?? false,
    };
  } catch {
    return null;
  }
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profile, setProfileState] = useState<UserProfile>(loadFromStorage);
  const [isSaving, setIsSaving]     = useState(false);

  // On mount: try to hydrate from backend (more up-to-date than localStorage)
  useEffect(() => {
    loadFromBackend().then((remote) => {
      if (remote && remote.mode) {
        setProfileState((prev) => ({ ...prev, ...remote }));
      }
    });
  }, []);

  const saveProfile = useCallback(async (updates: Partial<UserProfile>) => {
    setIsSaving(true);
    const next = { ...profile, ...updates };
    setProfileState(next);
    saveToStorage(next);
    try {
      await syncToBackend(next);
    } catch {}
    setIsSaving(false);
  }, [profile]);

  const setMode = useCallback(async (mode: OperationMode) => {
    await saveProfile({ mode });
  }, [saveProfile]);

  const isSetupComplete =
    profile.productDescription.trim().length > 0 ||
    profile.targetIndustries.length > 0 ||
    profile.skills.length > 0;

  return (
    <ProfileContext.Provider value={{ profile, isSetupComplete, isSaving, saveProfile, setMode }}>
      {children}
    </ProfileContext.Provider>
  );
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useProfile(): ProfileContextType {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used within <ProfileProvider>');
  return ctx;
}

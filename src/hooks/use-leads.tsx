"use client";

import { useState, createContext, useContext, ReactNode, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Lead, BackendLead } from '@/types/lead';
import { mapBackendLeadsToLeads } from '@/lib/lead-mapper';
import { getAuthHeader } from '@/lib/auth-client';

interface LeadContextType {
  leads: Lead[];
  isLoading: boolean;
  error: string | null;
  setLeads: (leads: Lead[]) => void;
  refreshLeads: () => Promise<void>;
  selectedLead: Lead | null;
  setSelectedLead: (lead: Lead | null) => void;
  updateLead: (id: string, updates: Partial<Lead>) => Promise<{ success: boolean; error?: string }>;
}

const LeadContext = createContext<LeadContextType | undefined>(undefined);

// ── Data Fetching ────────────────────────────────────────────────────────────

async function fetchLeads(): Promise<Lead[]> {
  const res = await fetch('/api/leads', {
    headers: getAuthHeader(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }
  const data = await res.json();
  const raw = Array.isArray(data.leads) ? data.leads : [];
  return mapBackendLeadsToLeads(raw as BackendLead[]);
}

async function patchLead(id: string, updates: Record<string, unknown>): Promise<void> {
  const res = await fetch(`/api/lead/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error ?? `HTTP ${res.status}`);
  }
}

// ── Provider ─────────────────────────────────────────────────────────────────

export function LeadProvider({ children }: { children: ReactNode }) {
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const queryClient = useQueryClient();

  const {
    data: leads = [],
    isLoading,
    error,
    refetch,
  } = useQuery<Lead[], Error>({
    queryKey: ['leads'],
    queryFn: fetchLeads,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const refreshLeads = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const updateMutation = useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Record<string, unknown> }) =>
      patchLead(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leads'] });
    },
  });

  const updateLead = useCallback(
    async (id: string, updates: Partial<Lead>): Promise<{ success: boolean; error?: string }> => {
      try {
        await updateMutation.mutateAsync({ id, updates });
        return { success: true };
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Update failed';
        return { success: false, error: message };
      }
    },
    [updateMutation]
  );

  const setLeads = useCallback(
    (newLeads: Lead[]) => {
      queryClient.setQueryData(['leads'], newLeads);
    },
    [queryClient]
  );

  return (
    <LeadContext.Provider
      value={{
        leads,
        isLoading,
        error: error?.message ?? null,
        setLeads,
        refreshLeads,
        selectedLead,
        setSelectedLead,
        updateLead,
      }}
    >
      {children}
    </LeadContext.Provider>
  );
}

export function useLeads() {
  const context = useContext(LeadContext);
  if (!context) throw new Error('useLeads must be used within LeadProvider');
  return context;
}

"use client";

import { useState, createContext, useContext, ReactNode, useEffect, useCallback } from 'react';
import { Lead } from '@/types/lead';
import { demoLeads } from '@/data/demo-leads';

interface LeadContextType {
  leads: Lead[];
  isLoading: boolean;
  error: string | null;
  setLeads: (leads: Lead[]) => void;
  refreshLeads: () => Promise<void>;
  selectedLead: Lead | null;
  setSelectedLead: (lead: Lead | null) => void;
}

const LeadContext = createContext<LeadContextType | undefined>(undefined);

export function LeadProvider({ children }: { children: ReactNode }) {
  const [leads, setLeads] = useState<Lead[]>(demoLeads);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  const refreshLeads = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/leads');
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data.leads) && data.leads.length > 0) {
        setLeads(data.leads);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch leads';
      setError(message);
      // Keep demo data on error — graceful degradation
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshLeads();
  }, [refreshLeads]);

  return (
    <LeadContext.Provider value={{ leads, isLoading, error, setLeads, refreshLeads, selectedLead, setSelectedLead }}>
      {children}
    </LeadContext.Provider>
  );
}

export function useLeads() {
  const context = useContext(LeadContext);
  if (!context) throw new Error('useLeads must be used within LeadProvider');
  return context;
}

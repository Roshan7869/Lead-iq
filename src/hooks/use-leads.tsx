import { useState, createContext, useContext, ReactNode } from 'react';
import { Lead } from '@/types/lead';
import { demoLeads } from '@/data/demo-leads';

interface LeadContextType {
  leads: Lead[];
  setLeads: (leads: Lead[]) => void;
  selectedLead: Lead | null;
  setSelectedLead: (lead: Lead | null) => void;
}

const LeadContext = createContext<LeadContextType | undefined>(undefined);

export function LeadProvider({ children }: { children: ReactNode }) {
  const [leads, setLeads] = useState<Lead[]>(demoLeads);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  return (
    <LeadContext.Provider value={{ leads, setLeads, selectedLead, setSelectedLead }}>
      {children}
    </LeadContext.Provider>
  );
}

export function useLeads() {
  const context = useContext(LeadContext);
  if (!context) throw new Error('useLeads must be used within LeadProvider');
  return context;
}

"use client";

/**
 * AppShell — wraps the entire authenticated app.
 *
 * Responsibilities:
 *  1. Shows <ProfileSetupWizard> automatically when profile is incomplete.
 *  2. Provides a "Setup Profile" trigger accessible from anywhere.
 *  3. Renders children (the actual page content) unchanged.
 *
 * The login page bypasses this because it renders outside the main layout
 * tree (src/app/login/layout.tsx is standalone).
 */

import { useState, Fragment, ReactNode } from 'react';
import dynamic from 'next/dynamic';
import { useProfile } from '@/hooks/use-profile';
import { usePathname } from 'next/navigation';

// Lazy-load the wizard — never needed on first paint
const ProfileSetupWizard = dynamic(
  () => import('@/components/profile-setup-wizard').then((m) => ({ default: m.ProfileSetupWizard })),
  { ssr: false },
);

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { isSetupComplete }       = useProfile();
  const [wizardOpen, setWizardOpen] = useState(false);
  const pathname                    = usePathname();

  // Don't show wizard on login page
  const isLoginPage = pathname?.startsWith('/login');

  // Auto-open wizard once on first visit when profile not configured
  // We track "seen" in sessionStorage so it only prompts once per session
  const [autoTriggered, setAutoTriggered] = useState(false);

  function maybeAutoOpen() {
    if (autoTriggered || isLoginPage || isSetupComplete) return;
    if (typeof sessionStorage !== 'undefined') {
      const seen = sessionStorage.getItem('leadiq:wizard_seen');
      if (!seen) {
        sessionStorage.setItem('leadiq:wizard_seen', '1');
        setWizardOpen(true);
        setAutoTriggered(true);
      }
    }
  }

  // Trigger check on render (runs once client-side)
  if (!autoTriggered && !isLoginPage && typeof window !== 'undefined') {
    maybeAutoOpen();
  }

  return (
    <Fragment>
      {children}

      {!isLoginPage && (
        <ProfileSetupWizard
          open={wizardOpen}
          onClose={() => setWizardOpen(false)}
        />
      )}
    </Fragment>
  );
}

// Export trigger so AppSidebar can open the wizard
export { };

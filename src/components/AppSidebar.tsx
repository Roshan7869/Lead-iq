"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Kanban,
  Search,
  Terminal,
  TrendingUp,
  Zap,
  ChevronLeft,
  ChevronRight,
  Settings2,
  LogOut,
} from 'lucide-react';
import { useState } from 'react';
import dynamic from 'next/dynamic';
import { cn } from '@/lib/utils';
import { ThemeToggle } from './ThemeToggle';
import { useAuth } from '@/hooks/use-auth';
import { useProfile } from '@/hooks/use-profile';

const ProfileSetupWizard = dynamic(
  () => import('@/components/profile-setup-wizard').then((m) => ({ default: m.ProfileSetupWizard })),
  { ssr: false },
);

const navItems = [
  { title: 'Overview', url: '/', icon: LayoutDashboard },
  { title: 'Pipeline', url: '/pipeline', icon: Kanban },
  { title: 'Demand Miner', url: '/demand-miner', icon: Search },
  { title: 'Command Center', url: '/command-center', icon: Terminal },
  { title: 'ROI Tracker', url: '/roi-tracker', icon: TrendingUp },
];

export function AppSidebar() {
  const [collapsed, setCollapsed]     = useState(false);
  const [wizardOpen, setWizardOpen]   = useState(false);
  const pathname                       = usePathname();
  const { username, isLoggedIn, logout } = useAuth();
  const { isSetupComplete }            = useProfile();

  return (
    <>
      <aside
        className={cn(
          'h-screen sticky top-0 flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300',
          collapsed ? 'w-16' : 'w-60'
        )}
      >
        {/* Logo & Theme Toggle */}
        <div className="flex items-center justify-between px-4 h-16 border-b border-sidebar-border">
          <div className="flex items-center gap-2 overflow-hidden">
            <Zap className="h-6 w-6 text-primary shrink-0" />
            {!collapsed && (
              <span className="text-foreground font-bold text-lg tracking-tight truncate">LeadIQ</span>
            )}
          </div>
          {!collapsed && <ThemeToggle />}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto custom-scrollbar">
          {navItems.map((item) => {
            const isActive = pathname === item.url;
            return (
              <Link
                key={item.url}
                href={item.url}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                  isActive && 'bg-sidebar-accent text-primary glow-primary',
                )}
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {!collapsed && <span>{item.title}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Bottom actions */}
        <div className="px-2 pb-3 space-y-1 border-t border-sidebar-border pt-3">
          {/* Profile setup button — highlight if not complete */}
          <button
            onClick={() => setWizardOpen(true)}
            className={cn(
              'flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
              isSetupComplete
                ? 'text-sidebar-foreground hover:bg-sidebar-accent'
                : 'text-amber-400 hover:bg-amber-400/10 bg-amber-400/5',
            )}
          >
            <Settings2 className="h-5 w-5 shrink-0" />
            {!collapsed && (
              <span className="truncate">
                {isSetupComplete ? 'Profile' : '⚠ Setup Profile'}
              </span>
            )}
          </button>

          {/* User / Logout */}
          {isLoggedIn && (
            <button
              onClick={logout}
              className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent transition-colors"
            >
              <LogOut className="h-5 w-5 shrink-0" />
              {!collapsed && (
                <span className="truncate">{username ?? 'Logout'}</span>
              )}
            </button>
          )}
        </div>

        {/* Collapse */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center h-12 border-t border-sidebar-border text-muted-foreground hover:text-foreground transition-colors"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </aside>

      <ProfileSetupWizard open={wizardOpen} onClose={() => setWizardOpen(false)} />
    </>
  );
}


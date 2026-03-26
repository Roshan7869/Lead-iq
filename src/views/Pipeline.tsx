"use client";

import dynamic from 'next/dynamic';
import { DashboardLayout } from '@/components/DashboardLayout';
import { Text } from '@/components/ui/text';

const EnhancedPipelineBoard = dynamic(
  () => import('@/components/enhanced/enhanced-pipeline-board').then((m) => ({ default: m.EnhancedPipelineBoard })),
  { ssr: false, loading: () => <div className="h-64 glass-panel animate-pulse" /> }
);

const LeadDetailModal = dynamic(
  () => import('@/components/LeadDetailModal').then((m) => ({ default: m.LeadDetailModal })),
  { ssr: false }
);

export default function PipelinePage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="animate-slide-up">
          <Text variant="h1" className="text-gradient">
            🚀 Lead Pipeline
          </Text>
          <Text variant="body" color="muted" className="mt-2">
            AI-powered lead management across all stages
          </Text>
        </div>

        <EnhancedPipelineBoard />
      </div>

      <LeadDetailModal />
    </DashboardLayout>
  );
}

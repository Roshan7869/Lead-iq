import { DashboardLayout } from '@/components/DashboardLayout';
import { EnhancedPipelineBoard } from '@/components/enhanced/enhanced-pipeline-board';
import { LeadDetailModal } from '@/components/LeadDetailModal';
import { Text } from '@/components/ui/text';

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

import { DashboardLayout } from '@/components/DashboardLayout';
import { EnhancedCommandCenter } from '@/components/enhanced/enhanced-command-center';
import { Text } from '@/components/ui/text';

export default function CommandCenterPage() {

  return (
    <DashboardLayout>
      <div className="space-y-4">
        <div className="animate-slide-up">
          <Text variant="h1" className="text-gradient">
            🧠 AI Command Center
          </Text>
          <Text variant="body" color="muted" className="mt-2">
            Advanced terminal interface with AI-powered insights
          </Text>
        </div>

        <EnhancedCommandCenter />
      </div>
    </DashboardLayout>
  );
}

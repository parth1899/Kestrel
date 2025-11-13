import { ThreatTimeline } from './ThreatTimeline';
import { ThreatDisposition } from './ThreatDisposition';
import { EndpointAnalysis } from './EndpointAnalysis';
import { ResponseAssignments } from './ResponseAssignments';
import { MitreTechniques } from './MitreTechniques';
import { SOCMetrics } from './SOCMetrics';
import { AlertsTable } from './AlertsTable';
import { DecisionQueue } from './DecisionQueue';
import { Sidebar } from './layout/Sidebar';
import { TopBar } from './layout/TopBar';
import { Card } from './ui/Card';

export function Dashboard() {
  return (
    <div className="min-h-screen flex bg-[var(--color-bg)] text-[var(--color-text)]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <TopBar />
        <main className="p-6 space-y-8">
          <div className="grid grid-cols-1 2xl:grid-cols-3 gap-6">
            <div className="2xl:col-span-2 space-y-6">
              <SOCMetrics />
              <ThreatDisposition />
            </div>
            <div className="space-y-6">
              <ThreatTimeline />
              <EndpointAnalysis />
            </div>
          </div>
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2 space-y-6">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <AlertsTable />
                <DecisionQueue />
              </div>
              <MitreTechniques />
            </div>
            <div className="space-y-6">
              <Card title="Operational KPIs">
                <div className="grid grid-cols-2 gap-4">
                  <Kpi label="Monthly Saved" value="$12.4K" tone="low" />
                  <Kpi label="Automation Rate" value="94.2%" tone="action" />
                  <Kpi label="Avg Response" value="2.1s" tone="medium" />
                  <Kpi label="Endpoints Protected" value="1,247" tone="high" />
                </div>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function Kpi({ label, value, tone }: { label: string; value: string; tone: string }) {
  const colorMap: Record<string, string> = {
    low: 'text-[var(--color-low)]',
    medium: 'text-[var(--color-medium)]',
    high: 'text-[var(--color-high)]',
    critical: 'text-[var(--color-critical)]',
    action: 'text-[var(--color-accent)]'
  };
  return (
    <div className="rounded-md bg-[var(--color-surface-alt)] p-4 border border-[var(--color-border)] flex flex-col gap-1">
      <div className={`text-xl font-semibold ${colorMap[tone]}`}>{value}</div>
      <div className="text-xs uppercase tracking-wide text-[var(--color-text-dim)]">{label}</div>
    </div>
  );
}
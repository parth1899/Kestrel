import { ThreatTimeline } from './ThreatTimeline';
import { ThreatDisposition } from './ThreatDisposition';
import { EndpointAnalysis } from './EndpointAnalysis';
import { ResponseAssignments } from './ResponseAssignments';
import { MitreTechniques } from './MitreTechniques';
import { SOCMetrics } from './SOCMetrics';
import { AlertsTable } from './AlertsTable';

export function Dashboard() {
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-white">Endpoint Security Platform</h1>
        <div className="text-right">
          <div className="text-sm text-gray-400">Cloud & On-Prem Resources</div>
          <div className="text-lg font-semibold text-blue-400">Kestrel</div>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <div className="xl:col-span-2">
          <SOCMetrics />
        </div>
        <div>
          <ThreatTimeline />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <div className="xl:col-span-2">
          <ThreatDisposition />
        </div>
        <div>
          <EndpointAnalysis />
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <ResponseAssignments />
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Cost Optimization</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="text-2xl font-bold text-green-400">$12.4K</div>
              <div className="text-sm text-gray-400">Monthly Saved</div>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-400">94.2%</div>
              <div className="text-sm text-gray-400">Automation Rate</div>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="text-2xl font-bold text-yellow-400">2.1s</div>
              <div className="text-sm text-gray-400">Avg Response Time</div>
            </div>
            <div className="bg-gray-700 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-400">1,247</div>
              <div className="text-sm text-gray-400">Endpoints Protected</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <AlertsTable />
        <MitreTechniques />
      </div>
    </div>
  );
}
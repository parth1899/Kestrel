import { useEffect, useState } from 'react';
import { fetchAlerts, Alert } from '../lib/api';

const severityColor: Record<string, string> = {
  critical: 'text-red-400',
  high: 'text-orange-400',
  medium: 'text-yellow-300',
  low: 'text-green-400',
};

export function AlertsTable() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severity, setSeverity] = useState<string>('');
  const [eventType, setEventType] = useState<string>('');

  useEffect(() => {
    setLoading(true);
    fetchAlerts({ limit: 50, severity: severity || undefined, event_type: eventType || undefined })
      .then(setAlerts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [severity, eventType]);

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Recent Alerts</h3>
        <div className="flex gap-2">
          <select aria-label="Filter by severity"
            className="bg-gray-700 text-white px-2 py-1 rounded"
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select aria-label="Filter by event type"
            className="bg-gray-700 text-white px-2 py-1 rounded"
            value={eventType}
            onChange={(e) => setEventType(e.target.value)}
          >
            <option value="">All Types</option>
            <option value="process">Process</option>
            <option value="network">Network</option>
            <option value="file">File</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>
      {loading ? (
        <div className="text-gray-400">Loading…</div>
      ) : error ? (
        <div className="text-red-400">{error}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-gray-400">
                <th className="text-left pb-2">Time</th>
                <th className="text-left pb-2">Severity</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2">Score</th>
                <th className="text-left pb-2">Agent</th>
                <th className="text-left pb-2">Key</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="border-t border-gray-700">
                  <td className="py-2 text-gray-300">{new Date(a.timestamp).toLocaleString()}</td>
                  <td className={`py-2 font-semibold ${severityColor[a.severity] || 'text-gray-200'}`}>{a.severity}</td>
                  <td className="py-2 text-gray-300">{a.event_type}</td>
                  <td className="py-2 text-gray-300">{a.score.toFixed(2)}</td>
                  <td className="py-2 text-gray-300">{a.agent_id}</td>
                  <td className="py-2 text-gray-400 truncate max-w-[240px]">
                    {a.details?.features?.process_name || a.details?.features?.remote_ip || a.event_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

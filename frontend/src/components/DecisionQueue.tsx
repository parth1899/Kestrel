import { useEffect, useState } from 'react';
import { API_BASE } from '../lib/api';

type Decision = {
  id: string;
  alert_id: string;
  agent_id: string;
  event_type: string;
  severity: string;
  score: number;
  recommended_action: string;
  priority: number;
  rationale?: Record<string, any>;
  status: string;
  created_at?: string;
  updated_at?: string;
};

export function DecisionQueue() {
  const [items, setItems] = useState<Decision[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetch(`${API_BASE}/api/decisions?status=pending`)
      .then((r) => r.json())
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const act = async (id: string, action: 'execute' | 'dismiss') => {
    await fetch(`${API_BASE}/api/decisions/${id}/${action}`, { method: 'POST' });
    load();
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <div className="flex justify-between mb-4">
        <h3 className="text-lg font-semibold">Decision Queue</h3>
        <button className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1 rounded" onClick={load}>Refresh</button>
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
                <th className="text-left pb-2">Created</th>
                <th className="text-left pb-2">Agent</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2">Severity</th>
                <th className="text-left pb-2">Score</th>
                <th className="text-left pb-2">Recommended Action</th>
                <th className="text-left pb-2">Priority</th>
                <th className="text-left pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {items.map((d) => (
                <tr key={d.id} className="border-t border-gray-700">
                  <td className="py-2 text-gray-300">{d.created_at ? new Date(d.created_at).toLocaleString() : ''}</td>
                  <td className="py-2 text-gray-300">{d.agent_id}</td>
                  <td className="py-2 text-gray-300">{d.event_type}</td>
                  <td className="py-2 text-gray-300">{d.severity}</td>
                  <td className="py-2 text-gray-300">{d.score.toFixed(2)}</td>
                  <td className="py-2 text-blue-300 font-semibold">{d.recommended_action}</td>
                  <td className="py-2 text-gray-300">{d.priority.toFixed(1)}</td>
                  <td className="py-2">
                    <div className="flex gap-2">
                      <button className="bg-green-600 hover:bg-green-500 text-white px-3 py-1 rounded" onClick={() => act(d.id, 'execute')}>Execute</button>
                      <button className="bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded" onClick={() => act(d.id, 'dismiss')}>Dismiss</button>
                    </div>
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

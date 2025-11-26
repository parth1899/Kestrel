import { useEffect, useMemo, useState } from 'react';
import { API_BASE } from '../lib/api';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Skeleton } from './ui/Skeleton';

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

  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const pageCount = Math.ceil(items.length / pageSize) || 1;
  const pageData = useMemo(() => items.slice((page - 1) * pageSize, page * pageSize), [items, page]);
  return (
    <Card
      title="Decision Queue"
      actions={<button className="px-3 py-1 rounded-md bg-[var(--color-accent)] text-white text-xs hover:brightness-110 focus-ring" onClick={load}>Refresh</button>}
    >
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={`skeleton-${i}`} height={18} />
          ))}
        </div>
      ) : error ? (
        <div className="text-red-400 text-sm">{error}</div>
      ) : (
        <div className="overflow-x-auto overflow-y-auto max-h-96 scrollbar-thin">
          <table className="min-w-full table-grid">
            <thead>
              <tr className="text-[var(--color-text-dim)]">
                <th className="text-left pb-2">Created</th>
                <th className="text-left pb-2">Agent</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2">Severity</th>
                <th className="text-left pb-2">Score</th>
                <th className="text-left pb-2">Action</th>
                <th className="text-left pb-2">Priority</th>
                <th className="text-left pb-2">Ops</th>
              </tr>
            </thead>
            <tbody>
              {pageData.map(d => (
                <>
                  <tr key={d.id} className="border-t border-[var(--color-border)] cursor-pointer hover:bg-[var(--color-surface-alt)]" onClick={()=>setExpandedId(expandedId===d.id?null:d.id)}>
                    <td className="py-2 text-xs whitespace-nowrap">{d.created_at ? new Date(d.created_at).toLocaleTimeString() : ''}</td>
                    <td className="py-2 text-xs text-[var(--color-text-dim)]">{d.agent_id}</td>
                    <td className="py-2 text-xs text-[var(--color-text-dim)]">{d.event_type}</td>
                    <td className="py-2"><Badge tone={d.severity as any}>{d.severity}</Badge></td>
                    <td className="py-2 text-xs font-mono">{d.score.toFixed(2)}</td>
                    <td className="py-2"><Badge tone="action">{d.recommended_action}</Badge></td>
                    <td className="py-2 text-xs text-[var(--color-text-dim)]">{d.priority.toFixed(1)}</td>
                    <td className="py-2">
                      <div className="flex gap-2">
                        <button className="px-2 py-1 rounded-md bg-green-600 text-white text-xs hover:brightness-110 focus-ring" onClick={(e)=>{e.stopPropagation(); act(d.id, 'execute');}}>Exec</button>
                        <button className="px-2 py-1 rounded-md bg-gray-600 text-white text-xs hover:brightness-110 focus-ring" onClick={(e)=>{e.stopPropagation(); act(d.id, 'dismiss');}}>Dismiss</button>
                      </div>
                    </td>
                  </tr>
                  {expandedId === d.id && (
                    <tr className="border-t border-[var(--color-border)]">
                      <td colSpan={8} className="py-3 text-xs bg-[var(--color-surface-alt)]">
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(d.rationale || {}).map(([k,v]) => (
                            <span key={k} className="px-2 py-1 rounded-md bg-[var(--color-border)] text-[var(--color-text-dim)]">{k}: {String(v)}</span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-3 flex items-center justify-between text-[var(--color-text-dim)] text-xs">
        <div>Page {page} of {pageCount}</div>
        <div className="flex gap-2">
          <button
            disabled={page===1}
            onClick={() => setPage(p => Math.max(1, p-1))}
            className="px-2 py-1 rounded-md bg-[var(--color-surface-alt)] disabled:opacity-40 hover:bg-[var(--color-border)] focus-ring"
          >Prev</button>
          <button
            disabled={page===pageCount}
            onClick={() => setPage(p => Math.min(pageCount, p+1))}
            className="px-2 py-1 rounded-md bg-[var(--color-surface-alt)] disabled:opacity-40 hover:bg-[var(--color-border)] focus-ring"
          >Next</button>
        </div>
      </div>
    </Card>
  );
}

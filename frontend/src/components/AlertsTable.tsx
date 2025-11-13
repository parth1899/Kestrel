import { useEffect, useState, useMemo } from 'react';
import { fetchAlerts, Alert } from '../lib/api';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';
import { Skeleton } from './ui/Skeleton';

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
  const [sortKey, setSortKey] = useState<'timestamp' | 'severity' | 'score'>('timestamp');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  useEffect(() => {
    setLoading(true);
    fetchAlerts({ limit: 50, severity: severity || undefined, event_type: eventType || undefined })
      .then(setAlerts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [severity, eventType]);

  const sorted = useMemo(() => {
    const copy = [...alerts];
    copy.sort((a, b) => {
      let av: number | string = a[sortKey];
      let bv: number | string = b[sortKey];
      if (sortKey === 'timestamp') {
        av = new Date(a.timestamp).getTime();
        bv = new Date(b.timestamp).getTime();
      }
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
    return copy;
  }, [alerts, sortKey, sortDir]);

  const pageCount = Math.ceil(sorted.length / pageSize) || 1;
  const pageData = sorted.slice((page - 1) * pageSize, page * pageSize);

  const toggleSort = (key: typeof sortKey) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  return (
    <Card
      title="Recent Alerts"
      actions={(
        <div className="flex gap-2 items-center">
          <select
            aria-label="Filter by severity"
            className="bg-[var(--color-surface-alt)] text-white px-2 py-1 rounded-md focus-ring text-xs"
            value={severity}
            onChange={(e) => { setPage(1); setSeverity(e.target.value); }}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select
            aria-label="Filter by event type"
            className="bg-[var(--color-surface-alt)] text-white px-2 py-1 rounded-md focus-ring text-xs"
            value={eventType}
            onChange={(e) => { setPage(1); setEventType(e.target.value); }}
          >
            <option value="">All Types</option>
            <option value="process">Process</option>
            <option value="network">Network</option>
            <option value="file">File</option>
            <option value="system">System</option>
          </select>
        </div>
      )}
    >
      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} height={18} />
          ))}
        </div>
      ) : error ? (
        <div className="text-red-400 text-sm">{error}</div>
      ) : (
        <div className="overflow-x-auto scrollbar-thin">
          <table className="min-w-full table-grid">
            <thead>
              <tr className="text-[var(--color-text-dim)]">
                <th className="text-left pb-2 cursor-pointer" onClick={() => toggleSort('timestamp')}>Time {sortKey==='timestamp' && (sortDir==='asc'?'▲':'▼')}</th>
                <th className="text-left pb-2 cursor-pointer" onClick={() => toggleSort('severity')}>Severity {sortKey==='severity' && (sortDir==='asc'?'▲':'▼')}</th>
                <th className="text-left pb-2">Type</th>
                <th className="text-left pb-2 cursor-pointer" onClick={() => toggleSort('score')}>Score {sortKey==='score' && (sortDir==='asc'?'▲':'▼')}</th>
                <th className="text-left pb-2">Agent</th>
                <th className="text-left pb-2">Key</th>
              </tr>
            </thead>
            <tbody>
              {pageData.map((a) => (
                <tr key={a.id} className="border-t border-[var(--color-border)]">
                  <td className="py-2 text-[var(--color-text)] text-xs whitespace-nowrap">{new Date(a.timestamp).toLocaleString()}</td>
                  <td className="py-2"><Badge tone={a.severity as any}>{a.severity}</Badge></td>
                  <td className="py-2 text-[var(--color-text-dim)] text-xs">{a.event_type}</td>
                  <td className="py-2 text-[var(--color-text)] text-xs font-mono">{a.score.toFixed(2)}</td>
                  <td className="py-2 text-[var(--color-text-dim)] text-xs">{a.agent_id}</td>
                  <td className="py-2 text-[var(--color-text-dim)] text-xs truncate max-w-[180px]">
                    {a.details?.features?.process_name || a.details?.features?.remote_ip || a.event_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between mt-4 text-xs text-[var(--color-text-dim)]">
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
        </div>
      )}
    </Card>
  );
}

import { useEffect, useMemo, useState } from 'react';
import { fetchMetric, ThreatTimelinePoint, SecurityAssessmentRow } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Card } from './ui/Card';
import { Badge } from './ui/Badge';

function StatCard({ title, value, unit }: { title: string; value: string | number; unit?: string }) {
  return (
    <Card padded={true} className="p-0">
      <div className="flex flex-col gap-1">
        <div className="text-xs uppercase tracking-wide text-[var(--color-text-dim)]">{title}</div>
        <div className="text-xl font-semibold text-[var(--color-accent)]">{value}{unit ? ` ${unit}` : ''}</div>
      </div>
    </Card>
  );
}

export function SOCMetrics() {
  const [events24h, setEvents24h] = useState<number>(0);
  const [threatLevel, setThreatLevel] = useState<number>(1);
  const [securityScore, setSecurityScore] = useState<number>(0);
  const [activeAgents, setActiveAgents] = useState<number>(0);
  const [timeline, setTimeline] = useState<ThreatTimelinePoint[]>([]);
  const [classification, setClassification] = useState<{ event_type: string; count: number }[]>([]);
  const [assessment, setAssessment] = useState<SecurityAssessmentRow[]>([]);
  const [assessPage, setAssessPage] = useState(1);
  const assessPageSize = 10;

  useEffect(() => {
    fetchMetric<{ value: number }>('security-events-24h').then((r) => setEvents24h(r.value)).catch(() => setEvents24h(0));
    fetchMetric<{ value: number }>('current-threat-level').then((r) => setThreatLevel(r.value)).catch(() => setThreatLevel(1));
    fetchMetric<{ value: number }>('security-posture-score').then((r) => setSecurityScore(r.value)).catch(() => setSecurityScore(0));
    fetchMetric<{ value: number }>('active-agents').then((r) => setActiveAgents(r.value)).catch(() => setActiveAgents(0));
    fetchMetric<{ series: ThreatTimelinePoint[] }>('threat-timeline').then((r) => setTimeline(r.series)).catch(() => setTimeline([]));
    fetchMetric<{ items: { event_type: string; count: number }[] }>('event-classification').then((r) => setClassification(r.items)).catch(() => setClassification([]));
    fetchMetric<{ rows: SecurityAssessmentRow[] }>('security-assessment').then((r) => setAssessment(r.rows)).catch(() => setAssessment([]));
  }, []);

  const pieData = useMemo(() => classification.map((c) => ({ name: c.event_type, value: c.count })), [classification]);
  const assessPageCount = useMemo(() => Math.ceil(assessment.length / assessPageSize) || 1, [assessment.length]);
  const assessPageData = useMemo(
    () => assessment.slice((assessPage - 1) * assessPageSize, assessPage * assessPageSize),
    [assessment, assessPage]
  );

  useEffect(() => { setAssessPage(1); }, [assessment.length]);
  const colors = ['#60a5fa', '#f59e0b', '#34d399', '#ef4444', '#a78bfa'];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Security Events (24h)" value={events24h} />
        <StatCard title="Threat Level" value={threatLevel} />
        <StatCard title="Posture Score" value={securityScore} />
        <StatCard title="Active Agents" value={activeAgents} />
      </div>

      <Card title="Real-time Threat Detection">
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeline} margin={{ left: 8, right: 8 }}>
              <XAxis dataKey="time" tick={{ fill: '#9aa9b8', fontSize: 10 }} tickFormatter={(t: string) => new Date(t).toLocaleTimeString()} />
              <YAxis yAxisId="left" tick={{ fill: '#9aa9b8', fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#9aa9b8', fontSize: 10 }} />
              <Tooltip labelFormatter={(label: string) => new Date(label).toLocaleString()} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line yAxisId="left" type="monotone" dataKey="threat_level" name="Threat" stroke="#ef4444" dot={false} strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="security_index" name="Security" stroke="#3b82f6" dot={false} strokeWidth={2} />
              <Line yAxisId="left" type="monotone" dataKey="anomaly_level" name="Anomaly" stroke="#f59e0b" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <Card title="Event Classification" className="xl:col-span-1">
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={75} label>
                  {pieData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Security Assessment" className="xl:col-span-2">
          <div className="overflow-x-auto">
            <table className="min-w-full table-grid">
              <thead>
                <tr className="text-[var(--color-text-dim)]">
                  <th className="text-left pb-2">Last Seen</th>
                  <th className="text-left pb-2">Endpoint</th>
                  <th className="text-left pb-2">Agent</th>
                  <th className="text-left pb-2">Risk</th>
                  <th className="text-left pb-2">Score</th>
                  <th className="text-left pb-2">CPU%</th>
                  <th className="text-left pb-2">Mem%</th>
                  <th className="text-left pb-2">Disk%</th>
                  <th className="text-left pb-2">Category</th>
                </tr>
              </thead>
              <tbody>
                {assessPageData.map((r, i) => (
                  <tr key={i} className="border-t border-[var(--color-border)]">
                    <td className="py-2 text-xs whitespace-nowrap">{new Date(r.last_seen).toLocaleString()}</td>
                    <td className="py-2 text-xs text-[var(--color-text)]">{r.endpoint}</td>
                    <td className="py-2 text-xs text-[var(--color-text-dim)]">{r.agent_id.slice(0, 10)}…</td>
                    <td className="py-2 text-xs"><Badge tone={r.risk_level>6?'high':r.risk_level>4?'medium':'low'}>{r.risk_level}</Badge></td>
                    <td className="py-2 text-xs font-mono">{r.security_score.toFixed(1)}</td>
                    <td className="py-2 text-xs">{r.cpu.toFixed(1)}</td>
                    <td className="py-2 text-xs">{r.memory.toFixed(1)}</td>
                    <td className="py-2 text-xs">{r.disk.toFixed(1)}</td>
                    <td className="py-2 text-xs text-[var(--color-text-dim)]">{r.threat_category}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex items-center justify-between text-[var(--color-text-dim)] text-xs">
            <div>Page {assessPage} of {assessPageCount}</div>
            <div className="flex gap-2">
              <button
                disabled={assessPage===1}
                onClick={() => setAssessPage(p => Math.max(1, p-1))}
                className="px-2 py-1 rounded-md bg-[var(--color-surface-alt)] disabled:opacity-40 hover:bg-[var(--color-border)] focus-ring"
              >Prev</button>
              <button
                disabled={assessPage===assessPageCount}
                onClick={() => setAssessPage(p => Math.min(assessPageCount, p+1))}
                className="px-2 py-1 rounded-md bg-[var(--color-surface-alt)] disabled:opacity-40 hover:bg-[var(--color-border)] focus-ring"
              >Next</button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}

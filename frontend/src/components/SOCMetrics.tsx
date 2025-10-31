import { useEffect, useMemo, useState } from 'react';
import { fetchMetric, ThreatTimelinePoint, SecurityAssessmentRow } from '../lib/api';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

function StatCard({ title, value, unit }: { title: string; value: string | number; unit?: string }) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
      <div className="text-sm text-gray-400">{title}</div>
      <div className="text-2xl font-bold text-blue-300">{value}{unit ? ` ${unit}` : ''}</div>
    </div>
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
  const colors = ['#60a5fa', '#f59e0b', '#34d399', '#ef4444', '#a78bfa'];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="Security Events (24h)" value={events24h} />
        <StatCard title="Current Threat Level" value={threatLevel} />
        <StatCard title="Security Posture Score" value={securityScore} />
        <StatCard title="Active Agents" value={activeAgents} />
      </div>

      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold mb-4">Real-time Threat Detection</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={timeline} margin={{ left: 16, right: 16 }}>
              <XAxis dataKey="time" hide={false} tick={{ fill: '#9ca3af' }} tickFormatter={(t: string) => new Date(t).toLocaleTimeString()} />
              <YAxis yAxisId="left" tick={{ fill: '#9ca3af' }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: '#9ca3af' }} />
              <Tooltip labelFormatter={(label: string) => new Date(label).toLocaleString()} />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="threat_level" name="Threat Level" stroke="#ef4444" dot={false} />
              <Line yAxisId="right" type="monotone" dataKey="security_index" name="Security Index" stroke="#60a5fa" dot={false} />
              <Line yAxisId="left" type="monotone" dataKey="anomaly_level" name="Anomaly Level" stroke="#f59e0b" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <h3 className="text-lg font-semibold mb-4">Event Classification</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={90} label>
                  {pieData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 overflow-x-auto">
          <h3 className="text-lg font-semibold mb-4">Security Assessment</h3>
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-gray-400">
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
              {assessment.map((r, i) => (
                <tr key={i} className="border-t border-gray-700">
                  <td className="py-2 text-gray-300">{new Date(r.last_seen).toLocaleString()}</td>
                  <td className="py-2 text-gray-300">{r.endpoint}</td>
                  <td className="py-2 text-gray-400">{r.agent_id.slice(0, 12)}…</td>
                  <td className="py-2 text-gray-300">{r.risk_level}</td>
                  <td className="py-2 text-gray-300">{r.security_score.toFixed(1)}</td>
                  <td className="py-2 text-gray-300">{r.cpu.toFixed(1)}</td>
                  <td className="py-2 text-gray-300">{r.memory.toFixed(1)}</td>
                  <td className="py-2 text-gray-300">{r.disk.toFixed(1)}</td>
                  <td className="py-2 text-gray-300">{r.threat_category}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002";

export type Alert = {
  id: string;
  event_id: string;
  agent_id: string;
  event_type: string;
  score: number;
  severity: string;
  source: string;
  details: Record<string, any>;
  timestamp: string;
};

export async function fetchAlerts(params: Record<string, string | number | undefined> = {}): Promise<Alert[]> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) qs.set(k, String(v));
  });
  const res = await fetch(`${API_BASE}/api/alerts?${qs.toString()}`);
  if (!res.ok) throw new Error("Failed to fetch alerts");
  return res.json();
}

export async function fetchMetric<T = any>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api/metrics/${path}`);
  if (!res.ok) throw new Error(`Failed to fetch metric ${path}`);
  return res.json();
}

export type ThreatTimelinePoint = {
  time: string;
  threat_level: number;
  security_index: number;
  anomaly_level: number;
};

export type SecurityAssessmentRow = {
  last_seen: string;
  endpoint: string;
  agent_id: string;
  risk_level: number;
  security_score: number;
  cpu: number;
  memory: number;
  disk: number;
  threat_category: string;
};

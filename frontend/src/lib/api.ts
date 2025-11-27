export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002";
export const PLAYBOOK_API_BASE = import.meta.env.VITE_PLAYBOOK_API_URL || "http://localhost:9000";

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

// Playbook Engine Types
export type PlaybookStep = {
  name: string;
  action: string;
  params: Record<string, any>;
  on_error?: string;
};

export type Playbook = {
  id: string;
  version?: string;
  name?: string;
  description?: string;
  metadata?: {
    event_type: string;
    severity: string;
  };
  preconditions?: any[];
  steps: PlaybookStep[];
  rollback?: any[];
  created_at?: string;
};

export type ExecutionResult = {
  execution_id: string;
  playbook_id: string;
  agent_id: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  results: Array<{
    action: string;
    status: string;
    message?: string;
    error?: string;
  }>;
};

// Playbook Engine API
export async function generatePlaybook(alert: Alert): Promise<Playbook> {
  const res = await fetch(`${PLAYBOOK_API_BASE}/api/playbooks/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      event_type: alert.event_type,
      severity: alert.severity,
      agent_id: alert.agent_id,
      details: alert.details,
    }),
  });
  if (!res.ok) throw new Error("Failed to generate playbook");
  const result = await res.json();
  
  // If the API returns a status with path, extract the playbook ID and fetch it
  if (result.status === 'exists' || result.status === 'generated') {
    // Extract playbook ID from path (e.g., pb-process-medium.yaml -> pb-process-medium)
    const pathParts = result.path?.split(/[/\\]/); // Handle both / and \ for Windows paths
    const filename = pathParts?.[pathParts.length - 1];
    const playbookId = filename?.replace('.yaml', '') || `pb-${alert.event_type}-${alert.severity}`;
    console.log('Extracted playbook ID:', playbookId, 'from path:', result.path);
    return getPlaybook(playbookId);
  }
  
  return result;
}

export async function getPlaybook(playbookId: string): Promise<Playbook> {
  console.log('Fetching playbook:', playbookId, 'from', `${PLAYBOOK_API_BASE}/api/playbooks/${playbookId}`);
  const res = await fetch(`${PLAYBOOK_API_BASE}/api/playbooks/${playbookId}`);
  if (!res.ok) {
    const errorText = await res.text();
    console.error('Failed to fetch playbook:', res.status, errorText);
    throw new Error(`Failed to fetch playbook: ${res.status} ${errorText}`);
  }
  return res.json();
}

export async function executePlaybook(playbookId: string, alert: Alert): Promise<ExecutionResult> {
  const res = await fetch(`${PLAYBOOK_API_BASE}/api/executions/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      playbook_id: playbookId,
      alert: {
        event_type: alert.event_type,
        severity: alert.severity,
        agent_id: alert.agent_id,
        event_id: alert.event_id,
        details: alert.details,
      },
    }),
  });
  if (!res.ok) throw new Error("Failed to execute playbook");
  return res.json();
}

export async function getExecution(executionId: string): Promise<ExecutionResult> {
  const res = await fetch(`${PLAYBOOK_API_BASE}/api/executions/${executionId}`);
  if (!res.ok) throw new Error("Failed to fetch execution");
  return res.json();
}

export async function checkPlaybookHealth(): Promise<{ status: string }> {
  const res = await fetch(`${PLAYBOOK_API_BASE}/health`);
  if (!res.ok) throw new Error("Playbook engine unhealthy");
  return res.json();
}

import React, { useState, useEffect } from 'react';
import { fetchAlerts, Alert, checkPlaybookHealth } from '../../lib/api';
import { Card } from '../ui/Card';
import { PlaybookPanel } from './PlaybookPanel';

// Sample alerts for demo when management-plane isn't running
const DEMO_ALERTS: Alert[] = [
  {
    id: 'demo-1',
    event_id: 'evt-proc-001',
    agent_id: 'windows-agent-001',
    event_type: 'process',
    score: 95.0,
    severity: 'high',
    source: 'analytics',
    details: {
      pid: 4242,
      path: 'C:/Temp/mimikatz.exe',
      features: {
        process_name: 'mimikatz.exe',
        command_line_len: 120,
        is_system_parent: false,
        vt_positives: 50,
        hash_known_malicious: true,
        yara_hits_count: 3,
        threat_score: 95.0,
        proc_freq_per_hour: 40,
        is_suspicious_path: true
      }
    },
    timestamp: new Date().toISOString()
  },
  {
    id: 'demo-2',
    event_id: 'evt-net-001',
    agent_id: 'windows-agent-001',
    event_type: 'network',
    score: 75.0,
    severity: 'medium',
    source: 'analytics',
    details: {
      ip: '95.111.200.207',
      remote_port: 21669,
      protocol: 'TCP',
      direction: 'outbound'
    },
    timestamp: new Date(Date.now() - 300000).toISOString()
  },
  {
    id: 'demo-3',
    event_id: 'evt-file-001',
    agent_id: 'windows-agent-002',
    event_type: 'file',
    score: 68.0,
    severity: 'medium',
    source: 'analytics',
    details: {
      path: 'C:/Users/Public/suspicious.exe',
      operation: 'create',
      file_size: 524288
    },
    timestamp: new Date(Date.now() - 600000).toISOString()
  },
  {
    id: 'demo-4',
    event_id: 'evt-proc-002',
    agent_id: 'windows-agent-003',
    event_type: 'process',
    score: 82.0,
    severity: 'high',
    source: 'analytics',
    details: {
      pid: 8888,
      path: 'C:/Windows/Temp/cryptominer.exe',
      features: {
        process_name: 'cryptominer.exe',
        threat_score: 82.0,
        hash_known_malicious: true
      }
    },
    timestamp: new Date(Date.now() - 900000).toISOString()
  }
];

export function PlaybookDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
  const [useDemoMode, setUseDemoMode] = useState(false);

  useEffect(() => {
    loadAlerts();
    checkHealth();
    const interval = setInterval(loadAlerts, 30000);
    return () => clearInterval(interval);
  }, [useDemoMode]);

  const loadAlerts = async () => {
    if (useDemoMode) {
      setAlerts(DEMO_ALERTS);
      return;
    }
    
    try {
      const data = await fetchAlerts({ limit: 20 });
      setAlerts(data);
      if (data.length === 0) {
        // Auto-enable demo mode if no real alerts
        setUseDemoMode(true);
      }
    } catch (err) {
      console.error('Failed to load alerts:', err);
      // Enable demo mode on error
      setUseDemoMode(true);
    }
  };

  const checkHealth = async () => {
    try {
      await checkPlaybookHealth();
      setHealthStatus('healthy');
    } catch {
      setHealthStatus('unhealthy');
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Playbook Response Center</h1>
          <p className="text-sm text-[var(--color-text-dim)] mt-1">
            Automated threat response and remediation
            {useDemoMode && <span className="ml-2 text-yellow-400">(Demo Mode)</span>}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={() => setUseDemoMode(!useDemoMode)}
            className="px-3 py-1 text-xs rounded-md border border-[var(--color-border)] hover:bg-[var(--color-surface-alt)]"
          >
            {useDemoMode ? 'Use Live Alerts' : 'Use Demo Alerts'}
          </button>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${healthStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-[var(--color-text-dim)]">
              Engine {healthStatus === 'healthy' ? 'Online' : 'Offline'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts List */}
        <Card title={`Recent Alerts ${useDemoMode ? '(Demo)' : ''}`}>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-[var(--color-text-dim)] text-sm">
                <div className="mb-2">No alerts available</div>
                <button
                  onClick={() => setUseDemoMode(true)}
                  className="px-4 py-2 bg-[var(--color-action)] text-white rounded-md hover:opacity-90"
                >
                  Load Demo Alerts
                </button>
              </div>
            ) : (
              alerts.map((alert) => (
                <button
                  key={alert.id}
                  onClick={() => setSelectedAlert(alert)}
                  className={`w-full text-left p-3 rounded-md border transition ${
                    selectedAlert?.id === alert.id
                      ? 'border-[var(--color-action)] bg-[var(--color-action)]/10'
                      : 'border-[var(--color-border)] hover:bg-[var(--color-surface-alt)]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{alert.event_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      alert.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                      alert.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                  <div className="text-xs text-[var(--color-text-dim)]">
                    {alert.agent_id} • {new Date(alert.timestamp).toLocaleString()}
                  </div>
                </button>
              ))
            )}
          </div>
        </Card>

        {/* Playbook Panel */}
        <div>
          {selectedAlert ? (
            <PlaybookPanel
              alert={selectedAlert}
              onClose={() => setSelectedAlert(null)}
            />
          ) : (
            <Card title="Response Playbook">
              <div className="text-center py-12 text-[var(--color-text-dim)] text-sm">
                Select an alert to generate a response playbook
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

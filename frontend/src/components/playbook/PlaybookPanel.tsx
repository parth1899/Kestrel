import React, { useState } from 'react';
import { Alert, generatePlaybook, executePlaybook, Playbook, ExecutionResult } from '../../lib/api';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

type PlaybookPanelProps = {
  alert: Alert;
  onClose?: () => void;
};

export function PlaybookPanel({ alert, onClose }: PlaybookPanelProps) {
  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [execution, setExecution] = useState<ExecutionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const pb = await generatePlaybook(alert);
      console.log('Generated playbook:', pb);
      setPlaybook(pb);
    } catch (err) {
      console.error('Playbook generation error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate playbook');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!playbook) return;
    setLoading(true);
    setError(null);
    try {
      const exec = await executePlaybook(playbook.id, alert);
      setExecution(exec);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute playbook');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Automated Response Playbook">
      <div className="space-y-4">
        {/* Alert Info */}
        <div className="p-3 bg-[var(--color-surface-alt)] rounded-md">
          <div className="text-xs text-[var(--color-text-dim)] mb-1">Alert Details</div>
          <div className="flex items-center gap-2 mb-2">
            <Badge tone={alert.severity === 'high' ? 'high' : alert.severity === 'medium' ? 'medium' : 'low'}>
              {alert.severity}
            </Badge>
            <span className="text-sm">{alert.event_type}</span>
          </div>
          <div className="text-xs text-[var(--color-text-dim)]">Agent: {alert.agent_id}</div>
        </div>

        {/* Generate Playbook */}
        {!playbook && (
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="w-full px-4 py-2 bg-[var(--color-action)] text-white rounded-md hover:opacity-90 disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate Response Playbook'}
          </button>
        )}

        {/* Playbook Details */}
        {playbook && (
          <div className="space-y-3">
            <div className="p-3 bg-[var(--color-surface-alt)] rounded-md">
              <div className="font-medium mb-1">{playbook.name || playbook.id || 'Generated Playbook'}</div>
              <div className="text-xs text-[var(--color-text-dim)] mb-3">
                {playbook.description || 
                 `${playbook.metadata?.event_type || 'Event'} response - ${playbook.metadata?.severity || 'medium'} severity`}
              </div>
              
              {playbook.steps && playbook.steps.length > 0 ? (
                <>
                  <div className="text-xs font-semibold mb-2 text-[var(--color-text-dim)]">RESPONSE STEPS:</div>
                  <div className="space-y-2">
                    {playbook.steps.map((step, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs p-2 bg-[var(--color-bg)] rounded">
                        <span className="text-[var(--color-action)] font-bold">{idx + 1}.</span>
                        <div className="flex-1">
                          <div className="font-medium text-white mb-1">{step.name}</div>
                          <div className="text-[var(--color-action)] mb-1">Action: {step.action}</div>
                          <div className="text-[var(--color-text-dim)]">
                            {step.params && Object.entries(step.params)
                              .filter(([k]) => k !== 'agent_id')
                              .map(([k, v]) => (
                                <div key={k} className="ml-2">• {k}: <span className="text-white">{String(v)}</span></div>
                              ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <div className="text-xs text-[var(--color-text-dim)]">
                  No steps defined in playbook
                </div>
              )}
            </div>

            {!execution && (
              <button
                onClick={handleExecute}
                disabled={loading}
                className="w-full px-4 py-2 bg-[var(--color-high)] text-white rounded-md hover:opacity-90 disabled:opacity-50"
              >
                {loading ? 'Executing...' : 'Execute Playbook'}
              </button>
            )}
          </div>
        )}

        {/* Execution Results */}
        {execution && (
          <div className="p-3 bg-[var(--color-surface-alt)] rounded-md">
            <div className="flex items-center justify-between mb-3">
              <div className="text-xs font-semibold text-[var(--color-text-dim)]">EXECUTION STATUS</div>
              <Badge tone={execution.status === 'completed' ? 'action' : execution.status === 'failed' ? 'high' : 'medium'}>
                {execution.status}
              </Badge>
            </div>
            
            <div className="space-y-2">
              {execution.results.map((result, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs p-2 bg-[var(--color-bg)] rounded">
                  <span className={result.status === 'success' ? 'text-green-500' : 'text-red-500'}>
                    {result.status === 'success' ? '✓' : '✗'}
                  </span>
                  <div className="flex-1">
                    <div className="font-medium">{result.action}</div>
                    <div className="text-[var(--color-text-dim)]">{result.message || result.error}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-md text-xs text-red-400">
            {error}
          </div>
        )}

        {onClose && (
          <button
            onClick={onClose}
            className="w-full px-4 py-2 border border-[var(--color-border)] rounded-md hover:bg-[var(--color-surface-alt)]"
          >
            Close
          </button>
        )}
      </div>
    </Card>
  );
}

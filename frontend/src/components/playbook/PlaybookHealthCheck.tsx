import React, { useEffect, useState } from 'react';
import { checkPlaybookHealth, PLAYBOOK_API_BASE } from '../../lib/api';

export function PlaybookHealthCheck() {
  const [status, setStatus] = useState<'checking' | 'healthy' | 'unhealthy'>('checking');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      try {
        await checkPlaybookHealth();
        setStatus('healthy');
        setError(null);
      } catch (err) {
        setStatus('unhealthy');
        setError(err instanceof Error ? err.message : 'Connection failed');
      }
    };

    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 p-3 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)] shadow-lg">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${
          status === 'healthy' ? 'bg-green-500' :
          status === 'unhealthy' ? 'bg-red-500' :
          'bg-yellow-500 animate-pulse'
        }`} />
        <div className="text-xs">
          <div className="font-medium">Playbook Engine</div>
          <div className="text-[var(--color-text-dim)]">
            {status === 'healthy' && 'Connected'}
            {status === 'unhealthy' && (error || 'Offline')}
            {status === 'checking' && 'Checking...'}
          </div>
        </div>
      </div>
      <div className="text-[10px] text-[var(--color-text-dim)] mt-1">
        {PLAYBOOK_API_BASE}
      </div>
    </div>
  );
}

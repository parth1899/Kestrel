import React from 'react';

export function TopBar() {
  return (
    <div className="flex items-center justify-between px-6 h-16 border-b border-[var(--color-border)] bg-[var(--color-surface)]">      
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold tracking-wide">Security Operations</h1>
        <span className="text-xs px-2 py-1 rounded bg-[var(--color-surface-alt)] text-[var(--color-text-dim)]">v1.0</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right">
          <div className="text-xs text-[var(--color-text-dim)]">Environment</div>
          <div className="text-sm font-medium">Production</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-[var(--color-surface-alt)] flex items-center justify-center text-sm font-semibold">OP</div>
        </div>
      </div>
    </div>
  );
}
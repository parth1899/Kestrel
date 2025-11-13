import React from 'react';
import { Badge } from '../ui/Badge';

const navItems = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'alerts', label: 'Alerts' },
  { key: 'decisions', label: 'Decisions' },
  { key: 'endpoints', label: 'Endpoints' },
  { key: 'analytics', label: 'Analytics' },
];

export function Sidebar() {
  return (
    <aside className="hidden lg:flex flex-col w-60 shrink-0 px-4 py-6 border-r border-[var(--color-border)] bg-[var(--color-surface)]">
      <div className="mb-8">
        <div className="text-xl font-semibold tracking-wide">Kestrel</div>
        <div className="text-xs text-[var(--color-text-dim)] mt-1">Endpoint Defense</div>
      </div>
      <nav className="flex-1 space-y-1">
        {navItems.map(item => (
          <button
            key={item.key}
            className="w-full text-left px-3 py-2 rounded-md text-sm text-[var(--color-text-dim)] hover:text-[var(--color-text)] hover:bg-[var(--color-surface-alt)] focus-ring transition"
          >{item.label}</button>
        ))}
      </nav>
      <div className="mt-6 p-3 rounded-md bg-[var(--color-surface-alt)]">
        <div className="text-xs uppercase font-semibold tracking-wide mb-2 text-[var(--color-text-dim)]">Status</div>
        <Badge tone="action">Live</Badge>
      </div>
    </aside>
  );
}
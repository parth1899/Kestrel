import React, { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { PlaybookDashboard } from './components/playbook/PlaybookDashboard';
import { PlaybookHealthCheck } from './components/playbook/PlaybookHealthCheck';
import { Sidebar } from './components/layout/Sidebar';
import { TopBar } from './components/layout/TopBar';

function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'playbooks'>('dashboard');

  return (
    <div className="min-h-screen flex bg-[var(--color-bg)] text-[var(--color-text)]">
      <Sidebar currentView={currentView} onNavigate={setCurrentView} />
      <div className="flex-1 flex flex-col min-h-screen">
        <TopBar />
        <main>
          {currentView === 'dashboard' && <Dashboard />}
          {currentView === 'playbooks' && <PlaybookDashboard />}
        </main>
      </div>
      <PlaybookHealthCheck />
    </div>
  );
}

export default App;
import React from 'react';
import { Shield } from 'lucide-react';

export function MitreTechniques() {
  const techniques = [
    { id: 'T1055', name: 'Process Injection', category: 'Defense Evasion', count: 23, risk: 'high' },
    { id: 'T1059', name: 'Command and Scripting', category: 'Execution', count: 34, risk: 'critical' },
    { id: 'T1005', name: 'Data from Local System', category: 'Collection', count: 12, risk: 'medium' },
    { id: 'T1083', name: 'File Discovery', category: 'Discovery', count: 18, risk: 'medium' },
    { id: 'T1021', name: 'Remote Services', category: 'Lateral Movement', count: 8, risk: 'high' },
    { id: 'T1027', name: 'Obfuscated Files', category: 'Defense Evasion', count: 15, risk: 'high' },
    { id: 'T1003', name: 'OS Credential Dumping', category: 'Credential Access', count: 6, risk: 'critical' },
    { id: 'T1012', name: 'Query Registry', category: 'Discovery', count: 28, risk: 'low' },
  ];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      'Execution': 'bg-purple-600',
      'Defense Evasion': 'bg-red-600',
      'Collection': 'bg-green-600',
      'Discovery': 'bg-blue-600',
      'Lateral Movement': 'bg-orange-600',
      'Credential Access': 'bg-pink-600',
    };
    return colors[category] || 'bg-gray-600';
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
        <Shield className="h-5 w-5 text-blue-400" />
        MITRE ATT&CK Techniques by Endpoint Risk
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {techniques.map((technique, index) => (
          <div key={index} className="bg-gray-700 p-4 rounded-lg hover:bg-gray-600 transition-colors cursor-pointer">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-gray-400">{technique.id}</span>
              <div className={`w-3 h-3 rounded-full ${getRiskColor(technique.risk)}`}></div>
            </div>
            <h4 className="font-semibold text-sm mb-2 leading-tight">{technique.name}</h4>
            <div className={`inline-block px-2 py-1 rounded text-xs text-white mb-2 ${getCategoryColor(technique.category)}`}>
              {technique.category}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">Detections:</span>
              <span className="font-bold text-white">{technique.count}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-600">
        <div className="flex flex-wrap gap-6 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Critical Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span>High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span>Medium Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Low Risk</span>
          </div>
        </div>
      </div>
    </div>
  );
}
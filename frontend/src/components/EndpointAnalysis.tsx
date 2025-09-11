import React from 'react';
import { Monitor, Server, Cloud, Smartphone } from 'lucide-react';

export function EndpointAnalysis() {
  const endpointData = [
    { type: 'Windows Desktop', count: 834, status: 'Protected', icon: Monitor, risk: 'Low' },
    { type: 'Linux Servers', count: 247, status: 'Monitoring', icon: Server, risk: 'Medium' },
    { type: 'Cloud Instances', count: 156, status: 'Secured', icon: Cloud, risk: 'Low' },
    { type: 'Mobile Devices', count: 89, status: 'Enrolled', icon: Smartphone, risk: 'High' },
  ];

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'text-green-400';
      case 'Medium': return 'text-yellow-400';
      case 'High': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Protected': return 'bg-green-900 text-green-300';
      case 'Secured': return 'bg-green-900 text-green-300';
      case 'Monitoring': return 'bg-blue-900 text-blue-300';
      case 'Enrolled': return 'bg-purple-900 text-purple-300';
      default: return 'bg-gray-900 text-gray-300';
    }
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-lg font-semibold mb-6">Endpoint Analysis</h3>
      
      <div className="space-y-4">
        {endpointData.map((endpoint, index) => {
          const IconComponent = endpoint.icon;
          return (
            <div key={index} className="flex items-center justify-between p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors">
              <div className="flex items-center gap-3">
                <IconComponent className="h-6 w-6 text-blue-400" />
                <div>
                  <div className="font-medium">{endpoint.type}</div>
                  <div className="text-sm text-gray-400">{endpoint.count} endpoints</div>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-xs px-2 py-1 rounded ${getStatusColor(endpoint.status)} mb-1`}>
                  {endpoint.status}
                </div>
                <div className={`text-xs font-medium ${getRiskColor(endpoint.risk)}`}>
                  {endpoint.risk} Risk
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-600">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Total Endpoints:</span>
          <span className="font-semibold">1,326</span>
        </div>
        <div className="flex justify-between text-sm mt-2">
          <span className="text-gray-400">Coverage:</span>
          <span className="font-semibold text-green-400">98.7%</span>
        </div>
      </div>
    </div>
  );
}
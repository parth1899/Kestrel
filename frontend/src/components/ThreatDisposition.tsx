import React from 'react';
import { CheckCircle, AlertCircle, XCircle, HelpCircle, Shield, Eye } from 'lucide-react';

export function ThreatDisposition() {
  const dispositions = [
    { label: 'True Positive', count: 8, percentage: '1.2%', color: 'text-green-400', icon: CheckCircle, desc: 'Confirmed Threats' },
    { label: 'Benign Positive', count: 5, percentage: '0.7%', color: 'text-blue-400', icon: Shield, desc: 'Safe but Flagged' },
    { label: 'False Positive', count: 12, percentage: '1.8%', color: 'text-yellow-400', icon: AlertCircle, desc: 'Incorrectly Flagged' },
    { label: 'Inconclusive', count: 7, percentage: '1.0%', color: 'text-gray-400', icon: HelpCircle, desc: 'Needs Investigation' },
    { label: 'Undetermined', count: 623, percentage: '93.1%', color: 'text-purple-400', icon: Eye, desc: 'Under Analysis' },
    { label: 'Other', count: 3, percentage: '0.4%', color: 'text-orange-400', icon: XCircle, desc: 'Miscellaneous' },
  ];

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-lg font-semibold mb-6">AI Analysis Disposition</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {dispositions.map((item, index) => {
          const IconComponent = item.icon;
          return (
            <div key={index} className="text-center">
              <div className="bg-gray-700 p-4 rounded-lg hover:bg-gray-600 transition-colors cursor-pointer">
                <IconComponent className={`h-8 w-8 mx-auto mb-2 ${item.color}`} />
                <div className={`text-2xl font-bold ${item.color}`}>
                  {item.count}
                </div>
                <div className={`text-sm ${item.color}`}>
                  {item.percentage}
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  {item.desc}
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {item.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
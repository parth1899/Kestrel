import React from 'react';
import { Shield, AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';

export function EndpointSummary() {
  const threatData = [
    { level: 'Critical', count: 23, color: 'bg-red-500', new: 2, investigating: 8, resolved: 13 },
    { level: 'High', count: 67, color: 'bg-orange-500', new: 5, investigating: 24, resolved: 38 },
    { level: 'Medium', count: 142, color: 'bg-yellow-500', new: 12, investigating: 43, resolved: 87 },
    { level: 'Low', count: 89, color: 'bg-blue-500', new: 7, investigating: 15, resolved: 67 },
    { level: 'Informational', count: 34, color: 'bg-gray-500', new: 3, investigating: 8, resolved: 23 },
  ];

  const totalThreats = threatData.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
        <Shield className="h-6 w-6 text-blue-400" />
        Threat Summary
      </h2>
      
      <div className="flex flex-col lg:flex-row gap-6">
        <div className="flex-shrink-0">
          <div className="relative w-48 h-48 mx-auto">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#374151"
                strokeWidth="8"
              />
              {/* Critical */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#EF4444"
                strokeWidth="8"
                strokeDasharray={`${(23/totalThreats) * 283} 283`}
                strokeDashoffset="0"
              />
              {/* High */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#F97316"
                strokeWidth="8"
                strokeDasharray={`${(67/totalThreats) * 283} 283`}
                strokeDashoffset={`-${(23/totalThreats) * 283}`}
              />
              {/* Medium */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#EAB308"
                strokeWidth="8"
                strokeDasharray={`${(142/totalThreats) * 283} 283`}
                strokeDashoffset={`-${((23+67)/totalThreats) * 283}`}
              />
              {/* Low */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#3B82F6"
                strokeWidth="8"
                strokeDasharray={`${(89/totalThreats) * 283} 283`}
                strokeDashoffset={`-${((23+67+142)/totalThreats) * 283}`}
              />
              {/* Informational */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#6B7280"
                strokeWidth="8"
                strokeDasharray={`${(34/totalThreats) * 283} 283`}
                strokeDashoffset={`-${((23+67+142+89)/totalThreats) * 283}`}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <div className="text-4xl font-bold text-white">{totalThreats}</div>
              <div className="text-sm text-gray-400">Total Threats</div>
            </div>
          </div>
        </div>

        <div className="flex-1">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-gray-400 border-b border-gray-600">
                  <th className="pb-2">Severity</th>
                  <th className="pb-2 text-center">New</th>
                  <th className="pb-2 text-center">Investigating</th>
                  <th className="pb-2 text-center">Resolved</th>
                  <th className="pb-2 text-center">Total</th>
                </tr>
              </thead>
              <tbody>
                {threatData.map((threat, index) => (
                  <tr key={index} className="border-b border-gray-700">
                    <td className="py-3">
                      <div className="flex items-center gap-3">
                        <div className={`w-4 h-4 rounded ${threat.color}`}></div>
                        <span>{threat.level}</span>
                      </div>
                    </td>
                    <td className="text-center py-3">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-900 text-blue-300 rounded text-xs">
                        <Clock className="h-3 w-3" />
                        {threat.new}
                      </span>
                    </td>
                    <td className="text-center py-3">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-900 text-yellow-300 rounded text-xs">
                        <AlertTriangle className="h-3 w-3" />
                        {threat.investigating}
                      </span>
                    </td>
                    <td className="text-center py-3">
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-900 text-green-300 rounded text-xs">
                        <CheckCircle className="h-3 w-3" />
                        {threat.resolved}
                      </span>
                    </td>
                    <td className="text-center py-3 font-semibold">{threat.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
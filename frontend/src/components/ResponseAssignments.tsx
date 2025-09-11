import React from 'react';
import { Users, Clock, CheckSquare, AlertTriangle } from 'lucide-react';

export function ResponseAssignments() {
  const analysts = [
    { name: 'Sarah Chen', new: 3, progress: 1, pending: 2, resolved: 8, total: 14 },
    { name: 'Mike Rodriguez', new: 2, progress: 0, pending: 1, resolved: 12, total: 15 },
    { name: 'AI Assistant', new: 458, progress: 23, pending: 7, resolved: 1247, total: 1735 },
    { name: 'Alex Thompson', new: 1, progress: 2, pending: 0, resolved: 6, total: 9 },
    { name: 'Emma Wilson', new: 0, progress: 1, pending: 1, resolved: 4, total: 6 },
  ];

  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
        <Users className="h-5 w-5 text-blue-400" />
        Response Assignments
      </h3>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-400 border-b border-gray-600">
              <th className="pb-3">Analyst</th>
              <th className="pb-3 text-center">New</th>
              <th className="pb-3 text-center">In Progress</th>
              <th className="pb-3 text-center">Pending</th>
              <th className="pb-3 text-center">Resolved</th>
              <th className="pb-3 text-center">Total</th>
            </tr>
          </thead>
          <tbody>
            {analysts.map((analyst, index) => (
              <tr key={index} className="border-b border-gray-700 hover:bg-gray-700 transition-colors">
                <td className="py-3">
                  <div className="flex items-center gap-3">
                    {analyst.name === 'AI Assistant' ? (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center">
                        <span className="text-xs font-bold">AI</span>
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                        <span className="text-xs font-bold">{analyst.name.split(' ').map(n => n[0]).join('')}</span>
                      </div>
                    )}
                    <span className={analyst.name === 'AI Assistant' ? 'text-purple-300' : ''}>{analyst.name}</span>
                  </div>
                </td>
                <td className="text-center py-3">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-900 text-blue-300 rounded text-xs">
                    <Clock className="h-3 w-3" />
                    {analyst.new}
                  </span>
                </td>
                <td className="text-center py-3">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-yellow-900 text-yellow-300 rounded text-xs">
                    <AlertTriangle className="h-3 w-3" />
                    {analyst.progress}
                  </span>
                </td>
                <td className="text-center py-3">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-orange-900 text-orange-300 rounded text-xs">
                    <Clock className="h-3 w-3" />
                    {analyst.pending}
                  </span>
                </td>
                <td className="text-center py-3">
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-900 text-green-300 rounded text-xs">
                    <CheckSquare className="h-3 w-3" />
                    {analyst.resolved}
                  </span>
                </td>
                <td className="text-center py-3 font-semibold">{analyst.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
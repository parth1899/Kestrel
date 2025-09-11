import React from 'react';
import { TrendingUp } from 'lucide-react';

export function ThreatTimeline() {
  return (
    <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-blue-400" />
        Threat Timeline
      </h3>
      
      <div className="mb-4">
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-blue-400"></div>
            <span className="text-gray-400">Informational</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-blue-500"></div>
            <span className="text-gray-400">Low</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-yellow-500"></div>
            <span className="text-gray-400">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-orange-500"></div>
            <span className="text-gray-400">High</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-red-500"></div>
            <span className="text-gray-400">Critical</span>
          </div>
        </div>
      </div>

      <div className="relative h-64">
        <svg className="w-full h-full" viewBox="0 0 400 200" preserveAspectRatio="none">
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="40" height="20" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 20" fill="none" stroke="#374151" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
          
          {/* Critical threats line */}
          <polyline
            points="0,180 40,175 80,170 120,165 160,155 200,145 240,140 280,135 320,130 360,125 400,120"
            fill="none"
            stroke="#EF4444"
            strokeWidth="2"
          />
          
          {/* High threats line */}
          <polyline
            points="0,160 40,155 80,150 120,145 160,140 200,130 240,125 280,120 320,115 360,110 400,105"
            fill="none"
            stroke="#F97316"
            strokeWidth="2"
          />
          
          {/* Medium threats line */}
          <polyline
            points="0,140 40,135 80,130 120,125 160,120 200,110 240,105 280,100 320,95 360,90 400,85"
            fill="none"
            stroke="#EAB308"
            strokeWidth="2"
          />
          
          {/* Low threats line */}
          <polyline
            points="0,120 40,115 80,110 120,105 160,100 200,95 240,90 280,85 320,80 360,75 400,70"
            fill="none"
            stroke="#3B82F6"
            strokeWidth="2"
          />
          
          {/* Informational threats line */}
          <polyline
            points="0,100 40,95 80,90 120,85 160,80 200,75 240,70 280,65 320,60 360,55 400,50"
            fill="none"
            stroke="#6B7280"
            strokeWidth="2"
          />
        </svg>
      </div>

      <div className="flex justify-between text-xs text-gray-400 mt-2">
        <span>6:00 AM</span>
        <span>8:00 AM</span>
        <span>10:00 AM</span>
        <span>12:00 PM</span>
        <span>2:00 PM</span>
        <span>4:00 PM</span>
        <span>6:00 PM</span>
      </div>
    </div>
  );
}
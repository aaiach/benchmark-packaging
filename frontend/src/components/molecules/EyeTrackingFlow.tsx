import React from 'react';
import { ChevronRight, Eye } from 'lucide-react';
import { Badge } from '../atoms/Badge';
import type { EyeTracking } from '../../types';

type EyeTrackingFlowProps = {
  eyeTracking: EyeTracking;
};

/**
 * Displays eye tracking analysis with pattern and flow.
 */
export function EyeTrackingFlow({ eyeTracking }: EyeTrackingFlowProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Badge variant="info" className="pl-2 pr-3">
          <Eye size={12} className="mr-1.5" />
          Pattern {eyeTracking.pattern_type}
        </Badge>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/30 rounded-lg p-2.5 border border-white/40">
          <span className="text-xs text-gray-500 block mb-1">Entrée</span>
          <span className="text-sm font-medium text-gray-800">{eyeTracking.entry_point}</span>
        </div>
        <div className="bg-white/30 rounded-lg p-2.5 border border-white/40">
          <span className="text-xs text-gray-500 block mb-1">Sortie</span>
          <span className="text-sm font-medium text-gray-800">{eyeTracking.exit_point}</span>
        </div>
      </div>

      {eyeTracking.fixation_sequence && eyeTracking.fixation_sequence.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2 p-3 bg-white/20 rounded-xl border border-white/30 backdrop-blur-sm">
          {eyeTracking.fixation_sequence.map((step, idx) => (
            <React.Fragment key={idx}>
              <span className="text-xs font-medium bg-white/60 px-2.5 py-1 rounded-md text-gray-700 shadow-sm border border-white/50">
                {step}
              </span>
              {idx < (eyeTracking.fixation_sequence?.length || 0) - 1 && (
                <ChevronRight size={14} className="text-gray-400 self-center" />
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}

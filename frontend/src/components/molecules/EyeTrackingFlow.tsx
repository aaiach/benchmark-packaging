import React from 'react';
import { ChevronRight } from 'lucide-react';
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
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm">
        <Badge variant="info">Pattern {eyeTracking.pattern_type}</Badge>
      </div>
      <div className="text-xs text-gray-400 space-y-1">
        <div>
          <span className="text-gray-300">Entrée :</span> {eyeTracking.entry_point}
        </div>
        <div>
          <span className="text-gray-300">Sortie :</span> {eyeTracking.exit_point}
        </div>
      </div>
      {eyeTracking.fixation_sequence && eyeTracking.fixation_sequence.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {eyeTracking.fixation_sequence.map((step, idx) => (
            <React.Fragment key={idx}>
              <span className="text-xs bg-white/10 px-2 py-1 rounded text-gray-300">
                {step}
              </span>
              {idx < (eyeTracking.fixation_sequence?.length || 0) - 1 && (
                <ChevronRight size={12} className="text-gray-600 self-center" />
              )}
            </React.Fragment>
          ))}
        </div>
      )}
    </div>
  );
}

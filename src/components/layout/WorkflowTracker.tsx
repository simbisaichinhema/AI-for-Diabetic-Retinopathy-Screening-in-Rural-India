/**
 * INFINITE LOOPS — SIH26038
 * Workflow Tracker — SIH-branded professional top header.
 * Shows: App name · Patient ID · Current step · Backend status
 */

import React from 'react';
import { Eye } from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

const STEP_LABELS: Record<string, string> = {
  acquisition:          '① Acquisition',
  quality_processing:   '② Quality Check',
  quality_results:      '③ Quality Report',
  analysis_processing:  '④ Screening',
  clinical_results:     '⑤ Clinical Results',
};

export const WorkflowTracker: React.FC = () => {
  const { exam, currentStep, navigateToStep } = useScreening();
  const stepKeys = Object.keys(STEP_LABELS);

  return (
    <header className="wt-header">
      {/* Left: Brand */}
      <div className="wt-brand">
        <div className="wt-eye-wrap">
          <Eye size={16} strokeWidth={2.2} />
        </div>
        <div className="wt-brand-text">
          <span className="wt-brand-name">SIH26038</span>
          <span className="wt-brand-tag">INFINITE LOOPS</span>
        </div>
      </div>

      {/* Center: Step tabs */}
      <nav className="wt-steps" aria-label="Workflow steps">
        {stepKeys.map((key) => {
          const isActive = currentStep === key;
          const isDone   = stepKeys.indexOf(key) < stepKeys.indexOf(currentStep);
          return (
            <button
              key={key}
              type="button"
              className={`wt-step ${isActive ? 'wt-step--active' : ''} ${isDone ? 'wt-step--done' : ''}`}
              onClick={() => navigateToStep(key as Parameters<typeof navigateToStep>[0])}
            >
              {STEP_LABELS[key]}
            </button>
          );
        })}
      </nav>

      {/* Right: Patient */}
      <div className="wt-right">
        {exam.patient.id && (
          <div className="wt-patient-chip">
            <span className="wt-chip-label">Patient</span>
            <span className="wt-chip-id">{exam.patient.id}</span>
          </div>
        )}
      </div>
    </header>
  );
};

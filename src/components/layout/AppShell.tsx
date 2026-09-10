/**
 * INFINITE LOOPS — SIH26038
 * Clinical Workstation Application Shell
 * session_start is a full-screen hero — no shell chrome.
 * Sidebar is ONLY shown in clinical_results (and is collapsible).
 */

import React from 'react';
import { WorkflowTracker } from './WorkflowTracker';
import { useScreening } from '../../context/ScreeningContext';
import { SessionStartPage } from '../session/SessionStartPage';
import { AcquisitionPage } from '../acquisition/AcquisitionPage';
import { QualityProcessingPage } from '../quality/QualityProcessingPage';
import { QualityResultsPage } from '../quality/QualityResultsPage';
import { AnalysisProcessingPage } from '../analysis/AnalysisProcessingPage';
import { ResultsDashboard } from '../results/ResultsDashboard';

export const AppShell: React.FC = () => {
  const { currentStep } = useScreening();

  const renderActiveStep = () => {
    switch (currentStep) {
      case 'session_start':
        return <SessionStartPage />;
      case 'acquisition':
        return <AcquisitionPage />;
      case 'quality_processing':
        return <QualityProcessingPage />;
      case 'quality_results':
        return <QualityResultsPage />;
      case 'analysis_processing':
        return <AnalysisProcessingPage />;
      case 'clinical_results':
        return <ResultsDashboard />;
      default:
        return <SessionStartPage />;
    }
  };

  return (
    <div className="clinical-app-shell">
      <div className="clinical-main-content">
        <WorkflowTracker />
        <main className={`clinical-page-container ${currentStep !== 'clinical_results' ? 'workflow-fullwidth' : ''}`}>
          {renderActiveStep()}
        </main>
      </div>
    </div>
  );
};

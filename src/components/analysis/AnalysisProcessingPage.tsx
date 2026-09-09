/**
 * INFINITE LOOPS — SIH26038
 * Screening Analysis Processing (Warm Clinical Workstation)
 * Clean, distraction-free deep learning screening with animated retinal radar scan.
 */

import React from 'react';
import {
  CheckCircle2,
  Loader2,
  Circle,
  ShieldCheck,
  Eye,
  Sparkles,
  Activity,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

export const AnalysisProcessingPage: React.FC = () => {
  const { analysisProgress, analysisEvents, exam } = useScreening();

  // Concise 4-point clinical screening stages
  const analysisStages = [
    {
      id: 'preprocessing',
      title: 'Preprocessing & FOV Alignment',
      desc: 'Contrast equalization, optic disc & macula anatomical alignment.',
      threshold: 30,
    },
    {
      id: 'feature_extraction',
      title: 'Deep Feature Representation',
      desc: 'EfficientNetB0 deep convolutional feature extraction.',
      threshold: 65,
    },
    {
      id: 'classification',
      title: 'DR Severity Grading',
      desc: 'Multi-class severity classification across Grades 0 through 4.',
      threshold: 85,
    },
    {
      id: 'explainability',
      title: 'Grad-CAM Attention & Report',
      desc: 'Attention heatmap mapping and clinical decision report compilation.',
      threshold: 100,
    },
  ];

  const latestEventMessage =
    analysisEvents.length > 0
      ? analysisEvents[analysisEvents.length - 1].message
      : 'Executing deep retinal screening pipeline…';

  // Dynamic color ramp: Red -> Orange -> Green
  const getProgressColor = (pct: number) => {
    if (pct < 35) return 'linear-gradient(90deg, #ef4444 0%, #f87171 100%)';
    if (pct < 75) return 'linear-gradient(90deg, #ef4444 0%, #f97316 100%)';
    return 'linear-gradient(90deg, #f97316 0%, #10b981 100%)';
  };

  const getBadgeColorClass = (pct: number) => {
    if (pct < 35) return 'text-red-500';
    if (pct < 75) return 'text-orange-500';
    return 'text-emerald-600';
  };

  return (
    <div className="ap-workstation">
      <div className="ap-card-container">
        {/* Header Strip */}
        <div className="ap-header-strip">
          <div className="ap-header-left">
            <div className="ap-step-badge">
              <Sparkles size={13} className="text-orange" />
              <span>STAGE 3 OF 4 · AI RETINAL SCREENING</span>
            </div>
            <h1 className="ap-main-title">Deep Retinal Screening Pipeline</h1>
            <p className="ap-main-subtitle">
              Evaluating bilateral vascular morphology, microvascular lesions & severity grading.
            </p>
          </div>

          <div className="ap-header-right">
            <div className="ap-patient-chip">
              <span className="p-chip-label">PATIENT</span>
              <span className="p-chip-val">{exam.patient.name}</span>
              <span className="p-chip-id">({exam.patient.id})</span>
            </div>
          </div>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="ap-progress-section">
          <div className="ap-progress-meta">
            <div className="ap-stage-status">
              <Loader2 size={15} className="animate-spin text-orange" />
              <span className="ap-stage-msg">{latestEventMessage}</span>
            </div>
            <div className={`ap-pct-badge ${getBadgeColorClass(analysisProgress)}`}>
              {analysisProgress}%
            </div>
          </div>
          <div className="ap-progress-track">
            <div
              className="ap-progress-fill"
              style={{
                width: `${analysisProgress}%`,
                background: getProgressColor(analysisProgress),
              }}
            />
          </div>
        </div>

        {/* Body Grid: Central Eye Radar Scan (Left) & Screening Pipeline Stages (Right) */}
        <div className="ap-body-grid">
          {/* Left: Animated convolutional network preview */}
          <div className="ap-radar-col">
            <div className="ap-col-label">
              <Eye size={14} className="text-slate-600" />
              <span>CONVOLUTIONAL FEATURE ENGINE</span>
            </div>

            <div className="ap-radar-card">
              <div className="ap-radar-viewport">
                <div className="ap-neural-network" aria-label="Animated neural network processing preview">
                  <div className="ap-neural-layer"><i /><i /><i /><i /><i /></div>
                  <div className="ap-neural-layer"><i /><i /><i /><i /><i /><i /></div>
                  <div className="ap-neural-layer"><i /><i /><i /><i /><i /></div>
                  <div className="ap-neural-layer"><i /><i /><i /></div>
                  <span className="ap-neural-pulse" />
                </div>

                {/* HUD Overlay Tags */}
                <div className="ap-radar-tag-top">
                  <Activity size={10} className="animate-pulse text-emerald" />
                  <span>LIVE FEATURE ACTIVATION</span>
                </div>
                <div className="ap-radar-tag-bottom">
                  <span>EFFICIENTNET-B0 / 5-CLASS CORAL</span>
                </div>
              </div>

              {/* Status Telemetry Strip */}
              <div className="ap-telemetry-row">
                <div className="ap-tel-item">
                  <span className="tel-lbl">RESOLUTION</span>
                  <span className="tel-val font-mono">224 × 224 RGB</span>
                </div>
                <div className="ap-tel-item">
                  <span className="tel-lbl">CHANNELS</span>
                  <span className="tel-val font-mono">3 (IMAGENET NORM)</span>
                </div>
                <div className="ap-tel-item">
                  <span className="tel-lbl">TARGETS</span>
                  <span className="tel-val font-mono">5 DR GRADES</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Clean 4-Stage Checklist */}
          <div className="ap-checklist-col">
            <div className="ap-col-label">
              <ShieldCheck size={14} className="text-slate-600" />
              <span>SCREENING STAGES</span>
            </div>

            <div className="ap-checklist-items">
              {analysisStages.map((stage) => {
                const isDone = analysisProgress >= stage.threshold;
                const isCurrent =
                  analysisProgress < stage.threshold &&
                  (analysisProgress >= stage.threshold - 30 || stage.threshold === 30);

                return (
                  <div
                    key={stage.id}
                    className={`ap-check-item ${isDone ? 'item-done' : isCurrent ? 'item-current' : 'item-pending'}`}
                  >
                    <div className="ap-item-icon">
                      {isDone ? (
                        <CheckCircle2 size={16} className="text-emerald" />
                      ) : isCurrent ? (
                        <Loader2 size={16} className="animate-spin text-orange" />
                      ) : (
                        <Circle size={16} className="text-slate-300" />
                      )}
                    </div>
                    <div className="ap-item-content">
                      <div className="ap-item-top">
                        <span className="ap-item-title">{stage.title}</span>
                        <span className={`ap-item-badge ${isDone ? 'badge-done' : isCurrent ? 'badge-current' : 'badge-pending'}`}>
                          {isDone ? 'Complete' : isCurrent ? 'Active' : 'Pending'}
                        </span>
                      </div>
                      <p className="ap-item-desc">{stage.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer info bar */}
        <div className="ap-footer-bar">
          <ShieldCheck size={15} className="text-emerald" />
          <span>NHM India Protocol · Real-time Deep Learning Diagnostic Synthesis</span>
        </div>
      </div>
    </div>
  );
};

import React from 'react';
import {
  CheckCircle2,
  Loader2,
  Circle,
  ShieldCheck,
  Eye,
  Sparkles,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

export const QualityProcessingPage: React.FC = () => {
  const { qualityProgress, qualityStageMessage, exam } = useScreening();

  // Simplified, compact 4-point criteria
  const qualityStages = [
    {
      id: 'focus',
      title: 'Vascular Edge Sharpness',
      desc: 'Laplacian focus score ≥ 100.0 for retinal microvasculature.',
      threshold: 25,
    },
    {
      id: 'illumination',
      title: 'Illumination Uniformity',
      desc: 'Exposure verification across macula and optic nerve head.',
      threshold: 50,
    },
    {
      id: 'fov',
      title: 'Field of View & Centering',
      desc: '45° diagnostic field centering with adequate anatomical coverage.',
      threshold: 75,
    },
    {
      id: 'integrity',
      title: 'Diagnostic Data Integrity',
      desc: 'Zero artifact or compression distortion confirmed.',
      threshold: 100,
    },
  ];

  // Dynamic color calculation: Red -> Orange -> Green
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
    <div className="qp-workstation">
      <div className="qp-card-container">
        {/* Header Strip */}
        <div className="qp-header-strip">
          <div className="qp-header-left">
            <div className="qp-step-badge">
              <Sparkles size={13} className="text-orange" />
              <span>STAGE 2 OF 4 · BILATERAL QUALITY GATE</span>
            </div>
            <h1 className="qp-main-title">Optical Quality Assessment</h1>
            <p className="qp-main-subtitle">
              Evaluating bilateral retinal vascular sharpness, luminance & anatomical coverage.
            </p>
          </div>

          <div className="qp-header-right">
            <div className="qp-patient-chip">
              <span className="p-chip-label">PATIENT</span>
              <span className="p-chip-val">{exam.patient.name}</span>
              <span className="p-chip-id">({exam.patient.id})</span>
            </div>
          </div>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="qp-progress-section">
          <div className="qp-progress-meta">
            <div className="qp-stage-status">
              <Loader2 size={15} className="animate-spin text-orange" />
              <span className="qp-stage-msg">{qualityStageMessage}</span>
            </div>
            <div className={`qp-pct-badge ${getBadgeColorClass(qualityProgress)}`}>
              {qualityProgress}%
            </div>
          </div>
          <div className="qp-progress-track">
            <div
              className="qp-progress-fill"
              style={{
                width: `${qualityProgress}%`,
                background: getProgressColor(qualityProgress),
              }}
            />
          </div>
        </div>

        {/* Dual Column Layout */}
        <div className="qp-body-grid">
          {/* Left: Dual Retinal Inspection Cards with Scanning Animation */}
          <div className="qp-retinal-col">
            <div className="qp-col-label">
              <Eye size={14} className="text-slate-600" />
              <span>ACQUIRED BILATERAL SCANS</span>
            </div>

            <div className="qp-eyes-row">
              {/* Left Eye OS */}
              <div className="qp-eye-card">
                <div className="qp-eye-header">
                  <span className="qp-eye-tag tag-os">LEFT EYE (OS)</span>
                  <span className="qp-eye-status">
                    {qualityProgress >= 50 ? (
                      <span className="status-done"><CheckCircle2 size={12} /> Assessed</span>
                    ) : (
                      <span className="status-scanning">Scanning…</span>
                    )}
                  </span>
                </div>
                <div className="qp-eye-frame">
                  {exam.leftEye.imageSrc ? (
                    <img src={exam.leftEye.imageSrc} alt="Left Eye OS" className="qp-eye-img" />
                  ) : (
                    <div className="qp-eye-placeholder">Left Eye Scan</div>
                  )}

                  {/* Scanning HUD Overlay & Moving Laser Line */}
                  <div className="qp-hud-grid" />
                  <div className="qp-scan-laser-line" />
                </div>
                <div className="qp-eye-metrics">
                  <div className="qp-m-row">
                    <span>Sharpness:</span>
                    <strong>{exam.leftEye.quality?.focus.score !== undefined ? `${exam.leftEye.quality.focus.score.toFixed(1)} measured` : 'Measuring...'}</strong>
                  </div>
                  <div className="qp-m-row">
                    <span>Illumination:</span>
                    <strong>{exam.leftEye.quality?.illumination.score !== undefined ? `${((exam.leftEye.quality.illumination.score / 255) * 100).toFixed(1)}% measured` : 'Measuring...'}</strong>
                  </div>
                </div>
              </div>

              {/* Right Eye OD */}
              <div className="qp-eye-card">
                <div className="qp-eye-header">
                  <span className="qp-eye-tag tag-od">RIGHT EYE (OD)</span>
                  <span className="qp-eye-status">
                    {qualityProgress >= 100 ? (
                      <span className="status-done"><CheckCircle2 size={12} /> Assessed</span>
                    ) : qualityProgress >= 50 ? (
                      <span className="status-scanning">Scanning…</span>
                    ) : (
                      <span className="status-waiting">Queued</span>
                    )}
                  </span>
                </div>
                <div className="qp-eye-frame">
                  {exam.rightEye.imageSrc ? (
                    <img src={exam.rightEye.imageSrc} alt="Right Eye OD" className="qp-eye-img" />
                  ) : (
                    <div className="qp-eye-placeholder">Right Eye Scan</div>
                  )}

                  {/* Scanning HUD Overlay & Moving Laser Line */}
                  <div className="qp-hud-grid" />
                  {qualityProgress >= 50 && <div className="qp-scan-laser-line" />}
                </div>
                <div className="qp-eye-metrics">
                  <div className="qp-m-row">
                    <span>Sharpness:</span>
                    <strong>{exam.rightEye.quality?.focus.score !== undefined ? `${exam.rightEye.quality.focus.score.toFixed(1)} measured` : 'Measuring...'}</strong>
                  </div>
                  <div className="qp-m-row">
                    <span>Illumination:</span>
                    <strong>{exam.rightEye.quality?.illumination.score !== undefined ? `${((exam.rightEye.quality.illumination.score / 255) * 100).toFixed(1)}% measured` : 'Measuring...'}</strong>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Simplified Stage Checklist */}
          <div className="qp-checklist-col">
            <div className="qp-col-label">
              <ShieldCheck size={14} className="text-slate-600" />
              <span>QUALITY CRITERIA</span>
            </div>

            <div className="qp-checklist-items">
              {qualityStages.map((stage) => {
                const isDone = qualityProgress >= stage.threshold;
                const isCurrent =
                  qualityProgress < stage.threshold &&
                  (qualityProgress >= stage.threshold - 25 || stage.threshold === 25);

                return (
                  <div
                    key={stage.id}
                    className={`qp-check-item ${isDone ? 'item-done' : isCurrent ? 'item-current' : 'item-pending'}`}
                  >
                    <div className="qp-item-icon">
                      {isDone ? (
                        <CheckCircle2 size={16} className="text-emerald" />
                      ) : isCurrent ? (
                        <Loader2 size={16} className="animate-spin text-orange" />
                      ) : (
                        <Circle size={16} className="text-slate-300" />
                      )}
                    </div>
                    <div className="qp-item-content">
                      <div className="qp-item-top">
                        <span className="qp-item-title">{stage.title}</span>
                        <span className={`qp-item-badge ${isDone ? 'badge-done' : isCurrent ? 'badge-current' : 'badge-pending'}`}>
                          {isDone ? 'Passed' : isCurrent ? 'Verifying' : 'Pending'}
                        </span>
                      </div>
                      <p className="qp-item-desc">{stage.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Footer info bar */}
        <div className="qp-footer-bar">
          <ShieldCheck size={15} className="text-emerald" />
          <span>Autonomous Clinical Validation · NHM India Protocol</span>
        </div>
      </div>
    </div>
  );
};

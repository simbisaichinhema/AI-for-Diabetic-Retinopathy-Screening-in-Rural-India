/**
 * INFINITE LOOPS — SIH26038
 * Quality Results Review (Warm Clinical Suite)
 * Clean, distraction-free bilateral quality report matching the session & acquisition workflow.
 */

import React, { useEffect, useRef } from 'react';
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  ArrowRight,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';
import { EyeData } from '../../types/clinical';

export const QualityResultsPage: React.FC = () => {
  const { exam, recaptureRejectedEye, runRetinalAnalysis } = useScreening();

  const leftQuality = exam.leftEye.quality;
  const rightQuality = exam.rightEye.quality;

  const isLeftAccepted = leftQuality?.overallStatus === 'ACCEPTED';
  const isRightAccepted = rightQuality?.overallStatus === 'ACCEPTED';
  const autoStarted = useRef(false);

  useEffect(() => {
    if (isLeftAccepted && isRightAccepted && !autoStarted.current) {
      autoStarted.current = true;
      const timer = window.setTimeout(() => runRetinalAnalysis(), 900);
      return () => window.clearTimeout(timer);
    }
  }, [isLeftAccepted, isRightAccepted, runRetinalAnalysis]);

  const renderEyeCard = (eye: EyeData, isAccepted: boolean) => {
    const q = eye.quality;
    const focusVal = q?.focus?.score !== undefined ? `${(q.focus.score / 4).toFixed(1)}% (Laplacian: ${q.focus.score.toFixed(1)})` : 'Unavailable';
    const illumVal = q?.illumination?.score !== undefined ? `${((q.illumination.score / 255) * 100).toFixed(1)}% (Measured)` : 'Unavailable';

    return (
      <div className="qr-eye-card">
        {/* Card Header */}
        <div className="qr-eye-header">
          <div className="qr-eye-title">
            <span className={`qr-eye-badge ${eye.side === 'OS' ? 'badge-os' : 'badge-od'}`}>
              {eye.sideLabel}
            </span>
          </div>
          <span className={`qr-status-pill ${isAccepted ? 'status-pass' : 'status-recapture'}`}>
            {isAccepted ? <CheckCircle2 size={13} /> : <XCircle size={13} />}
            <span>{isAccepted ? 'PASSED · ELIGIBLE' : 'RECAPTURE SUGGESTED'}</span>
          </span>
        </div>

        {/* Retinal Image Viewport */}
        <div className="qr-eye-frame">
          {eye.imageSrc ? (
            <img src={eye.imageSrc} alt={`${eye.sideLabel} Fundus`} className="qr-eye-img" />
          ) : (
            <div className="qr-empty-placeholder">No Image Available</div>
          )}
          <span className="qr-frame-tag">{eye.side} · RETINAL FUNDUS</span>
        </div>

        {/* Clean Metrics Table */}
        <div className="qr-metrics-list">
          <div className="qr-metric-row">
            <span className="m-label">Vascular Focus</span>
            <span className="m-value text-emerald">{focusVal}</span>
          </div>
          <div className="qr-metric-row">
            <span className="m-label">Illumination</span>
            <span className="m-value text-emerald">{illumVal}</span>
          </div>
          <div className="qr-metric-row">
            <span className="m-label">Field of View</span>
            <span className="m-value">{q?.fieldOfView.details || 'Unavailable'}</span>
          </div>
          <div className="qr-metric-row">
            <span className="m-label">Fundus Validity</span>
            <span className={`m-value ${q?.fundusValidity.isValid ? 'text-emerald' : 'text-red'}`}>
              {q?.fundusValidity.details || 'Unavailable'}
            </span>
          </div>
          <div className="qr-metric-row row-overall">
            <span className="m-label">Quality Gate</span>
            <span className={`m-value font-bold ${isAccepted ? 'text-emerald' : 'text-red'}`}>
              {q?.overallStatus || 'PENDING'}
            </span>
          </div>
        </div>

        {/* Retake Button if needed */}
        <button
          type="button"
          className="qr-retake-btn"
          onClick={() => recaptureRejectedEye(eye.side)}
        >
          <RotateCcw size={13} />
          <span>Retake {eye.sideLabel}</span>
        </button>
      </div>
    );
  };

  return (
    <div className="qr-workstation">
      <div className="qr-card-container">
        {/* Header Strip */}
        <div className="qr-header-strip">
          <div className="qr-header-left">
            <div className="qr-step-badge">
              <Sparkles size={13} className="text-orange" />
              <span>STAGE 2 OF 4 · QUALITY GATE VERIFICATION</span>
            </div>
            <h1 className="qr-main-title">Bilateral Quality Assessment Results</h1>
            <p className="qr-main-subtitle">
              {isLeftAccepted && isRightAccepted
                ? 'Both retinal scans satisfy the configured diagnostic quality thresholds.'
                : 'One or more retinal scans failed quality verification and require recapture.'}
            </p>
          </div>

          <div className="qr-header-right">
            <div className="qr-gate-status-badge">
              <ShieldCheck size={16} className="text-emerald" />
              <span>QUALITY GATE: {isLeftAccepted && isRightAccepted ? 'PASSED' : 'RECAPTURE REQUIRED'}</span>
            </div>
          </div>
        </div>

        {/* Bilateral Cards Grid */}
        <div className="qr-body-grid">
          {renderEyeCard(exam.leftEye, Boolean(isLeftAccepted))}
          {renderEyeCard(exam.rightEye, Boolean(isRightAccepted))}
        </div>

        {/* Action Bar */}
        <div className="qr-action-bar">
          <div className="qr-disclaimer">
            NHM India SIH26038 Automated Protocol · Images eligible for deep learning inference
          </div>

          <div className="qr-action-buttons">
            <button
              type="button"
              id="btn-run-analysis"
              className="qr-btn-primary"
              onClick={runRetinalAnalysis}
              disabled={!isLeftAccepted || !isRightAccepted}
            >
              <span>{isLeftAccepted && isRightAccepted ? 'Opening AI Results...' : 'Proceed to AI Retinal Analysis'}</span>
              <ArrowRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

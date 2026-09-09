/**
 * INFINITE LOOPS — SIH26038
 * Minimal Clinical Retinal Screening Dashboard (Results Workspace)
 * Operator/Clinician facing workstation layout with dense information hierarchy,
 * large retinal viewports, exact backend data, and explicit clinical review panel.
 */

import React, { useState } from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  History,
  Save,
  RotateCcw,
  ShieldCheck,
  Printer,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';
import { DR_GRADES, DRGradeIndex } from '../../types/clinical';
import { HistoryModal } from './HistoryModal';
import { ReportModal } from './ReportModal';

export const ResultsDashboard: React.FC = () => {
  const {
    exam,
    updateClinicalReview,
    saveClinicalReview,
    resetClinicalReview,
    setIsHistoryModalOpen,
    setIsReportModalOpen,
  } = useScreening();

  const [saveStatusMsg, setSaveStatusMsg] = useState<string | null>(null);
  const [isEditingReview, setIsEditingReview] = useState(false);
  const [leftEyeMode, setLeftEyeMode] = useState<'color' | 'gradcam' | 'enhanced'>('gradcam');
  const [rightEyeMode, setRightEyeMode] = useState<'color' | 'gradcam' | 'enhanced'>('gradcam');

  const leftEye = exam.leftEye;
  const rightEye = exam.rightEye;
  const overallGrade = exam.overallGrade;
  const overallGradeInfo = overallGrade === null ? null : DR_GRADES[overallGrade];
  const screeningInterpretation = overallGrade === 0
    ? 'No sufficient evidence to confirm diabetic retinopathy in the submitted images. This is a screening result, not a definitive diagnosis.'
    : overallGrade === null
    ? 'No valid AI screening interpretation is available yet.'
    : `AI screening indicates ${overallGradeInfo?.shortLabel || 'a retinal finding'}. Confirm the finding with qualified clinical review before care decisions.`;

  const isReviewDone = exam.clinicalReview.clinicalGrade !== null || Boolean(saveStatusMsg);

  const handleSave = async () => {
    const success = await saveClinicalReview();
    if (success) {
      setSaveStatusMsg('Clinical assessment saved.');
      setIsEditingReview(false);
      setTimeout(() => setSaveStatusMsg(null), 4000);
    }
  };

  const useAiAssessment = () => {
    if (overallGrade === null) return;
    updateClinicalReview({
      clinicalGrade: overallGrade,
      clinicalReferable: Boolean(exam.overallReferable),
    });
    setIsEditingReview(true);
  };

  const getEyeDisplaySrc = (eye: typeof leftEye, mode: 'color' | 'gradcam' | 'enhanced') => {
    if (mode === 'gradcam' && eye.gradCamSrc) return eye.gradCamSrc;
    if (mode === 'enhanced' && eye.enhancedSrc) return eye.enhancedSrc;
    return eye.imageSrc || '';
  };

  const getViewportLabel = (eye: typeof leftEye, mode: 'color' | 'gradcam' | 'enhanced') => {
    if (mode === 'gradcam' && !eye.gradCamAvailable) return 'MODEL ATTENTION UNAVAILABLE';
    if (mode === 'gradcam') return 'MODEL ATTENTION (GRAD-CAM)';
    if (mode === 'enhanced') return 'CLAHE CONTRAST ENHANCED';
    return 'ORIGINAL COLOR FUNDUS';
  };

  return (
    <div className="minimal-results-dashboard">
      {/* Top Examination Context Bar */}
      <div className="compact-exam-header-bar">
        <div className="exam-context-group">
          <div className="ctx-block">
            <span className="ctx-lbl">PATIENT ID</span>
            <span className="ctx-val font-mono">{exam.patient.id || 'UNREGISTERED'}</span>
          </div>
          <span className="ctx-divider">|</span>
          <div className="ctx-block">
            <span className="ctx-lbl">NAME</span>
            <span className="ctx-val">{exam.patient.name || 'Anonymous Patient'}</span>
          </div>
          <span className="ctx-divider">|</span>
          <div className="ctx-block">
            <span className="ctx-lbl">AGE / SEX</span>
            <span className="ctx-val">
              {exam.patient.age ? `${exam.patient.age} Yrs` : '—'} / {exam.patient.sex || '—'}
            </span>
          </div>
          <span className="ctx-divider">|</span>
          <div className="ctx-block">
            <span className="ctx-lbl">EXAM DATE</span>
            <span className="ctx-val">{exam.timestamp || 'Current Session'}</span>
          </div>
          <span className="ctx-divider">|</span>
          <div className="ctx-block">
            <span className="ctx-lbl">MODEL ENGINE</span>
            <span className="ctx-val font-mono">{exam.modelVersion || 'DR-EfficientNetB0'}</span>
          </div>
        </div>

        <div className="export-report-btn-wrap" style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn-report-history"
            onClick={() => setIsHistoryModalOpen(true)}
            title="View longitudinal screening history"
          >
            <History size={13} />
            <span>HISTORY</span>
          </button>
          <button
            type="button"
            className="btn-report-export"
            onClick={() => setIsReportModalOpen(true)}
            title="Open printable clinical report"
          >
            <Printer size={13} />
            <span>EXPORT CLINICAL REPORT</span>
          </button>
        </div>
      </div>

      <div className="dashboard-main-grid">
        {/* LEFT COLUMN (Primary Clinical Findings) */}
        <div className="dashboard-left-col">
          {/* Section 1: Top Clinical Banner */}
          <section className="dashboard-panel panel-banner">
            <div className="banner-top-row">
              <div className="banner-grade-badge">
                <span className="grade-pill-tag">AI SCREENING ASSESSMENT</span>
                <span className="grade-title-text">{overallGradeInfo?.label || 'AI result unavailable'}</span>
                <span className="grade-index-tag">GRADE {overallGrade ?? '—'} OF 4</span>
              </div>

              <div className="banner-referral-block">
                <span className="referral-status-lbl">REFERRAL RECOMMENDATION</span>
                <div className="referral-status-val">
                  {exam.overallReferable ? (
                    <span className="referral-pill refer-yes">
                      <AlertTriangle size={14} />
                      <span>REFERRAL REQUIRED</span>
                    </span>
                  ) : (
                    <span className="referral-pill refer-no">
                      <CheckCircle2 size={14} />
                      <span>NO REFERABLE FINDING IDENTIFIED</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            <p className="banner-desc-text">{screeningInterpretation}</p>
            <div className="banner-review-note"><ShieldCheck size={14} /> Ophthalmologist confirmation required before clinical decisions.</div>
          </section>

          {/* Section 2: Bilateral Retinal Imaging with GradCAM & Enhanced Toggles */}
          <section className="dashboard-panel panel-imaging">
            <div className="panel-sub-header">
              <span className="panel-title-sm">RETINAL IMAGING & AI EXPLAINABILITY</span>
              <span className="panel-tag-sm">OPTICAL VIEWPORTS</span>
            </div>

            <div className="retinal-imaging-grid">
              {/* Left Eye (OS) */}
              <div className="eye-imaging-column">
                <div className="eye-column-header">
                  <span className="eye-name">LEFT EYE · OS</span>
                  <div className="eye-mode-toggles">
                    <button
                      className={`mode-pill ${leftEyeMode === 'color' ? 'active' : ''}`}
                      onClick={() => setLeftEyeMode('color')}
                    >
                      Color
                    </button>
                    <button
                      className={`mode-pill ${leftEyeMode === 'gradcam' ? 'active' : ''}`}
                      onClick={() => setLeftEyeMode('gradcam')}
                    >
                      Grad-CAM
                    </button>
                    <button
                      className={`mode-pill ${leftEyeMode === 'enhanced' ? 'active' : ''}`}
                      onClick={() => setLeftEyeMode('enhanced')}
                    >
                      Enhanced
                    </button>
                  </div>
                </div>

                <div className="imaging-viewports-pair">
                  <div className="viewport-box">
                    <img
                      src={getEyeDisplaySrc(leftEye, leftEyeMode)}
                      alt={`Left Eye ${leftEyeMode}`}
                      className="viewport-img"
                    />
                    <span className={`viewport-label ${leftEyeMode === 'gradcam' && !leftEye.gradCamAvailable ? 'viewport-label-muted' : ''}`}>
                      {getViewportLabel(leftEye, leftEyeMode)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Eye (OD) */}
              <div className="eye-imaging-column">
                <div className="eye-column-header">
                  <span className="eye-name">RIGHT EYE · OD</span>
                  <div className="eye-mode-toggles">
                    <button
                      className={`mode-pill ${rightEyeMode === 'color' ? 'active' : ''}`}
                      onClick={() => setRightEyeMode('color')}
                    >
                      Color
                    </button>
                    <button
                      className={`mode-pill ${rightEyeMode === 'gradcam' ? 'active' : ''}`}
                      onClick={() => setRightEyeMode('gradcam')}
                    >
                      Grad-CAM
                    </button>
                    <button
                      className={`mode-pill ${rightEyeMode === 'enhanced' ? 'active' : ''}`}
                      onClick={() => setRightEyeMode('enhanced')}
                    >
                      Enhanced
                    </button>
                  </div>
                </div>

                <div className="imaging-viewports-pair">
                  <div className="viewport-box">
                    <img
                      src={getEyeDisplaySrc(rightEye, rightEyeMode)}
                      alt={`Right Eye ${rightEyeMode}`}
                      className="viewport-img"
                    />
                    <span className={`viewport-label ${rightEyeMode === 'gradcam' && !rightEye.gradCamAvailable ? 'viewport-label-muted' : ''}`}>
                      {getViewportLabel(rightEye, rightEyeMode)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Section 3: DR Severity Probability (Compact Table) */}
          <section className="dashboard-panel panel-probability">
            <div className="panel-sub-header">
              <span className="panel-title-sm">DR SEVERITY PROBABILITY</span>
              <span className="panel-tag-sm">PREDICTION DISTRIBUTION</span>
            </div>

            <table className="compact-prob-table">
              <thead>
                <tr>
                  <th>DR GRADE</th>
                  <th style={{ textAlign: 'right' }}>LEFT EYE (OS)</th>
                  <th style={{ textAlign: 'right' }}>RIGHT EYE (OD)</th>
                </tr>
              </thead>
              <tbody>
                {([
                  { gradeNum: 0, label: 'Grade 0 — No DR', k: 'grade0' },
                  { gradeNum: 1, label: 'Grade 1 — Mild DR', k: 'grade1' },
                  { gradeNum: 2, label: 'Grade 2 — Moderate DR', k: 'grade2' },
                  { gradeNum: 3, label: 'Grade 3 — Severe DR', k: 'grade3' },
                  { gradeNum: 4, label: 'Grade 4 — Proliferative DR', k: 'grade4' },
                ] as const).map((row) => {
                  const leftProb = leftEye.probabilities ? leftEye.probabilities[row.k] : null;
                  const rightProb = rightEye.probabilities ? rightEye.probabilities[row.k] : null;

                  return (
                    <tr key={row.k}>
                      <td className="grade-col">{row.label}</td>
                      <td className="prob-val-col">
                        {leftProb !== null ? `${(leftProb * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td className="prob-val-col">
                        {rightProb !== null ? `${(rightProb * 100).toFixed(1)}%` : '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="severity-bars" aria-label="Bilateral model probability bars">
              {([
                { label: 'No DR', key: 'grade0' },
                { label: 'Mild', key: 'grade1' },
                { label: 'Moderate', key: 'grade2' },
                { label: 'Severe', key: 'grade3' },
                { label: 'Proliferative', key: 'grade4' },
              ] as const).map((row) => (
                <div className="severity-bar-row" key={row.key}>
                  <span>{row.label}</span>
                  <div className="severity-bar-track"><span style={{ width: `${(leftEye.probabilities?.[row.key] || 0) * 100}%` }} /></div>
                  <b>{leftEye.probabilities ? `${(leftEye.probabilities[row.key] * 100).toFixed(0)}%` : '—'}</b>
                  <div className="severity-bar-track"><span className="severity-bar-right" style={{ width: `${(rightEye.probabilities?.[row.key] || 0) * 100}%` }} /></div>
                  <b>{rightEye.probabilities ? `${(rightEye.probabilities[row.key] * 100).toFixed(0)}%` : '—'}</b>
                </div>
              ))}
            </div>
          </section>

          {/* Section 4: Retinal Evidence */}
          <section className="dashboard-panel panel-evidence">
            <div className="panel-sub-header">
              <span className="panel-title-sm">RETINAL EVIDENCE</span>
              <span className="panel-tag-sm">Evidence source: computer-vision heuristics · review required</span>
            </div>

            <table className="compact-evidence-table">
              <thead>
                <tr>
                  <th>FINDING / LESION TYPE</th>
                  <th>LEFT EYE (OS)</th>
                  <th>RIGHT EYE (OD)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Microaneurysms</td>
                  <td>{leftEye.evidence?.microaneurysms ? `${leftEye.evidence.microaneurysms.count} (${(leftEye.evidence.microaneurysms.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                  <td>{rightEye.evidence?.microaneurysms ? `${rightEye.evidence.microaneurysms.count} (${(rightEye.evidence.microaneurysms.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                </tr>
                <tr>
                  <td>Hemorrhages</td>
                  <td>{leftEye.evidence?.hemorrhages ? `${leftEye.evidence.hemorrhages.count} (${(leftEye.evidence.hemorrhages.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                  <td>{rightEye.evidence?.hemorrhages ? `${rightEye.evidence.hemorrhages.count} (${(rightEye.evidence.hemorrhages.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                </tr>
                <tr>
                  <td>Exudates</td>
                  <td>{leftEye.evidence?.exudates ? `${leftEye.evidence.exudates.count} (${(leftEye.evidence.exudates.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                  <td>{rightEye.evidence?.exudates ? `${rightEye.evidence.exudates.count} (${(rightEye.evidence.exudates.confidence * 100).toFixed(0)}%)` : 'None'}</td>
                </tr>
                <tr>
                  <td>Vessel Abnormalities</td>
                  <td>{leftEye.evidence?.vesselAbnormalities || 'None'}</td>
                  <td>{rightEye.evidence?.vesselAbnormalities || 'None'}</td>
                </tr>
                <tr>
                  <td>Macular Involvement</td>
                  <td>{leftEye.evidence?.macularInvolvement ? 'Yes' : 'No'}</td>
                  <td>{rightEye.evidence?.macularInvolvement ? 'Yes' : 'No'}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>

        {/* SIDE COLUMN (~30%): DEDICATED CLINICAL REVIEW WORKSPACE */}
        <div className="dashboard-side-col">
          <div className="clinical-review-card">
            {/* Header with Review Status */}
            <div className="review-card-header">
              <span className="review-card-title">CLINICAL REVIEW</span>
              <span className={`review-status-pill ${isReviewDone ? 'done' : 'pending'}`}>
                {isReviewDone ? 'REVIEW COMPLETED' : 'PENDING REVIEW'}
              </span>
            </div>

            <div className="review-priority-note">
              <ShieldCheck size={15} />
              <div>
                <strong>Human review is the final clinical step</strong>
                <span>Confirm or amend the AI screening interpretation and record your reasoning.</span>
              </div>
            </div>

            {/* Readout of AI Assessment */}
            <div className="ai-readout-box">
              <div className="readout-lbl">AI ASSESSMENT PREDICTION</div>
              <div className="readout-val">
                {overallGradeInfo ? `Grade ${overallGrade} — ${overallGradeInfo.shortLabel}` : 'AI result unavailable'}
              </div>
            </div>

            {!isEditingReview && !isReviewDone ? (
              <div className="review-quick-actions">
                <p>Review the bilateral images, evidence, and probability bars before confirming the AI screening result.</p>
                <button type="button" className="btn-review-save" onClick={useAiAssessment} disabled={overallGrade === null}>
                  <CheckCircle2 size={14} />
                  <span>Use AI Result as Draft</span>
                </button>
                <button type="button" className="btn-review-reset" onClick={() => setIsEditingReview(true)}>
                  <span>Edit Assessment</span>
                </button>
              </div>
            ) : (
            /* Detailed form stays available on demand. */
            <div className="review-form-body">
              <div className="form-field-group">
                <label className="field-lbl" htmlFor="clinical-grade-select">Final Assessment (Grade)</label>
                <select
                  id="clinical-grade-select"
                  className="field-select"
                  value={exam.clinicalReview.clinicalGrade ?? (overallGrade === null ? '' : overallGrade)}
                  disabled={overallGrade === null}
                  onChange={(e) => updateClinicalReview({ clinicalGrade: Number(e.target.value) as DRGradeIndex })}
                >
                  <option value={0}>No DR (Grade 0)</option>
                  <option value={1}>Mild NPDR (Grade 1)</option>
                  <option value={2}>Moderate NPDR (Grade 2)</option>
                  <option value={3}>Severe NPDR (Grade 3)</option>
                  <option value={4}>PDR (Grade 4)</option>
                </select>
              </div>

              <div className="form-field-group">
                <span className="field-lbl">Referable DR?</span>
                <div className="radio-options-row">
                  <label className="radio-opt">
                    <input
                      type="radio"
                      name="clinical-referable-radio"
                      checked={exam.clinicalReview.clinicalReferable === false || (exam.clinicalReview.clinicalReferable === null && !exam.overallReferable)}
                      onChange={() => updateClinicalReview({ clinicalReferable: false })}
                    />
                    <span>No</span>
                  </label>
                  <label className="radio-opt">
                    <input
                      type="radio"
                      name="clinical-referable-radio"
                      checked={exam.clinicalReview.clinicalReferable === true || (exam.clinicalReview.clinicalReferable === null && !!exam.overallReferable)}
                      onChange={() => updateClinicalReview({ clinicalReferable: true })}
                    />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div className="form-field-group">
                <label className="field-lbl" htmlFor="reviewer-select">Reviewer</label>
                <select
                  id="reviewer-select"
                  className="field-select"
                  value={exam.clinicalReview.reviewerName}
                  onChange={(e) => updateClinicalReview({ reviewerName: e.target.value })}
                >
                  <option value="Dr. Sharma">Dr. Sharma (Ophthalmologist)</option>
                  <option value="Dr. A. Verma">Dr. A. Verma (Retina Specialist)</option>
                  <option value="Dr. R. Patel">Dr. R. Patel (Medical Officer)</option>
                </select>
              </div>

              <div className="form-field-group">
                <label className="field-lbl" htmlFor="clinical-notes-area">Clinical Notes</label>
                <textarea
                  id="clinical-notes-area"
                  className="field-textarea"
                  rows={4}
                  placeholder="Add clinical remarks, follow-up instructions, or diagnostic notes..."
                  value={exam.clinicalReview.clinicalNotes}
                  onChange={(e) => updateClinicalReview({ clinicalNotes: e.target.value })}
                />
              </div>

              {saveStatusMsg && (
                <div className="save-status-toast">
                  <ShieldCheck size={14} />
                  <span>{saveStatusMsg}</span>
                </div>
              )}

              <div className="review-actions-row">
                <button
                  type="button"
                  className="btn-review-save"
                  onClick={handleSave}
                >
                  <Save size={14} />
                  <span>Save Assessment</span>
                </button>

                <button
                  type="button"
                  className="btn-review-reset"
                  onClick={resetClinicalReview}
                >
                  <RotateCcw size={14} />
                  <span>Reset</span>
                </button>

                <button type="button" className="btn-review-reset" onClick={() => setIsEditingReview(false)}>
                  <span>Hide Details</span>
                </button>
              </div>
            </div>
            )}

            <div className="review-disclaimer-footer">
              AI-assisted screening prototype · Clinical review required.
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      <HistoryModal />
      <ReportModal />
    </div>
  );
};

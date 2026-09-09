/**
 * INFINITE LOOPS — SIH26038
 * Official Clinical Retinal Screening Report Document Preview & Print Module
 * Formatted as an official tele-ophthalmology diagnostic document with bilateral
 * retinal fundus image attachments, Grad-CAM maps, metrics, and signature block.
 */

import React from 'react';
import { X, Printer, Download, Eye, AlertCircle, ShieldCheck } from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';
import { apiService } from '../../services/api';
import { DR_GRADES } from '../../types/clinical';

export const ReportModal: React.FC = () => {
  const { exam, isReportModalOpen, setIsReportModalOpen } = useScreening();

  if (!isReportModalOpen) return null;

  const handlePrint = () => {
    window.print();
  };

  const handleExportCsv = () => {
    const csvContent = apiService.exportExamCsv(exam);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `DR_Report_${exam.patient.id.replace('#', '')}_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const overallGrade = exam.overallGrade ?? 0;
  const overallInfo = DR_GRADES[overallGrade];

  const leftEye = exam.leftEye;
  const rightEye = exam.rightEye;

  const clinicalGrade = exam.clinicalReview.clinicalGrade;
  const verifiedGradeLabel = clinicalGrade !== null ? `Grade ${clinicalGrade} — ${DR_GRADES[clinicalGrade].shortLabel}` : 'Unreviewed (Draft)';

  return (
    <div className="report-modal-overlay" onClick={() => setIsReportModalOpen(false)}>
      <div className="report-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Top Action Toolbar (Hidden during print) */}
        <div className="report-toolbar no-print">
          <div className="toolbar-title-group">
            <Eye size={16} className="text-blue-600" />
            <span>OFFICIAL CLINICAL RETINAL SCREENING REPORT PREVIEW</span>
          </div>

          <div className="toolbar-actions">
            <button type="button" className="btn-report-action" onClick={handleExportCsv}>
              <Download size={14} />
              <span>Export CSV</span>
            </button>

            <button type="button" className="btn-report-primary" onClick={handlePrint}>
              <Printer size={14} />
              <span>Print / Save PDF</span>
            </button>

            <button
              type="button"
              className="btn-report-close"
              onClick={() => setIsReportModalOpen(false)}
              title="Close Preview"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Printable Official Medical Document Container */}
        <div className="report-document-body printable-area">
          {/* Header Letterhead */}
          <div className="doc-letterhead">
            <div className="lh-left">
              <div className="lh-brand">
                <Eye size={24} color="#1e40af" strokeWidth={2.5} />
                <span className="lh-brand-name">INFINITE LOOPS</span>
              </div>
              <div className="lh-program">
                Rural Retinopathy Tele-Screening Program (SIH26038)
              </div>
              <div className="lh-sub">
                AI-Assisted Diagnostic Screening & Clinical Tele-Ophthalmology
              </div>
            </div>

            <div className="lh-right">
              <div className="doc-type-badge">OFFICIAL DIAGNOSTIC REPORT</div>
              <div className="lh-meta">
                <div><strong>Report Date:</strong> {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: '2-digit' })}</div>
                <div><strong>Exam ID:</strong> {exam.id || 'EXAM-853543'}</div>
                <div><strong>Model Engine:</strong> {exam.modelVersion}</div>
              </div>
            </div>
          </div>

          {/* Section 1: Patient Demographics & Exam Context */}
          <div className="doc-section">
            <div className="sec-header">PATIENT DEMOGRAPHICS & EXAM METADATA</div>
            <div className="demographics-grid">
              <div className="demo-item">
                <span className="lbl">Patient ID:</span>
                <span className="val font-mono">{exam.patient.id || 'UNREGISTERED'}</span>
              </div>
              <div className="demo-item">
                <span className="lbl">Full Name:</span>
                <span className="val">{exam.patient.name || 'Anonymous Patient'}</span>
              </div>
              <div className="demo-item">
                <span className="lbl">Age / Sex:</span>
                <span className="val">{exam.patient.age ? `${exam.patient.age} Yrs` : '—'} / {exam.patient.sex || '—'}</span>
              </div>
              <div className="demo-item">
                <span className="lbl">Division / Region:</span>
                <span className="val">{exam.patient.villageOrDistrict || 'Rural Screening Program'}</span>
              </div>
              <div className="demo-item">
                <span className="lbl">Examination Time:</span>
                <span className="val">{exam.timestamp || 'Current Session'}</span>
              </div>
              <div className="demo-item">
                <span className="lbl">System Operator:</span>
                <span className="val">{exam.clinicalReview.reviewerName || 'Unassigned'}</span>
              </div>
            </div>
          </div>

          {/* Section 2: AI Diagnostic Screening Result */}
          <div className="doc-section">
            <div className="sec-header">1. AI DIAGNOSTIC SCREENING ASSESSMENT</div>
            <div className="ai-result-summary-box">
              <div className="result-main-col">
                <div className="res-lbl">OVERALL AI SCREENING GRADE</div>
                <div className="res-grade-title">
                  Grade {overallGrade} — {overallInfo.label}
                </div>
                <div className="res-meta-line">
                  Model Confidence: <strong>{exam.overallConfidence !== null ? `${(exam.overallConfidence * 100).toFixed(1)}%` : '—'}</strong>
                  &nbsp;•&nbsp; Referable Probability P(referable): <strong>{exam.referableProbability !== null ? `${(exam.referableProbability * 100).toFixed(1)}%` : '—'}</strong>
                </div>
              </div>

              <div className={`result-status-col ${exam.overallReferable ? 'res-referable' : 'res-negative'}`}>
                <div className="status-main-text">
                  {exam.overallReferable ? 'REFERRAL RECOMMENDED' : 'NEGATIVE FOR REFERABLE DR'}
                </div>
                <div className="status-sub-text">
                  {exam.overallReferable ? 'Referable diabetic retinopathy thresholds met.' : 'No referable diabetic retinopathy detected.'}
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Bilateral Retinal Imaging Attachments (Visual Proof) */}
          <div className="doc-section page-break-inside-avoid">
            <div className="sec-header">2. BILATERAL RETINAL FUNDUS PHOTOGRAPHS & EXPLAINABILITY</div>
            <div className="doc-imaging-grid">
              {/* Left Eye (OS) */}
              <div className="doc-eye-column">
                <div className="eye-doc-title">LEFT EYE (OS) — COLOR FUNDUS & GRAD-CAM ATTENTION</div>
                <div className="doc-viewports-pair">
                  <div className="doc-vp">
                    {leftEye.imageSrc ? (
                      <img src={leftEye.imageSrc} alt="Left Eye Fundus" />
                    ) : (
                      <div className="vp-missing">No fundus image uploaded</div>
                    )}
                    <span className="vp-caption">OS Color Fundus Image</span>
                  </div>
                  <div className="doc-vp">
                    {leftEye.gradCamAvailable && leftEye.gradCamSrc ? (
                      <img src={leftEye.gradCamSrc} alt="Left Eye Grad-CAM" />
                    ) : (
                      <div className="vp-missing">Model attention unavailable</div>
                    )}
                    <span className="vp-caption">OS Model Attention (Grad-CAM)</span>
                  </div>
                </div>
              </div>

              {/* Right Eye (OD) */}
              <div className="doc-eye-column">
                <div className="eye-doc-title">RIGHT EYE (OD) — COLOR FUNDUS & GRAD-CAM ATTENTION</div>
                <div className="doc-viewports-pair">
                  <div className="doc-vp">
                    {rightEye.imageSrc ? (
                      <img src={rightEye.imageSrc} alt="Right Eye Fundus" />
                    ) : (
                      <div className="vp-missing">No fundus image uploaded</div>
                    )}
                    <span className="vp-caption">OD Color Fundus Image</span>
                  </div>
                  <div className="doc-vp">
                    {rightEye.gradCamAvailable && rightEye.gradCamSrc ? (
                      <img src={rightEye.gradCamSrc} alt="Right Eye Grad-CAM" />
                    ) : (
                      <div className="vp-missing">Model attention unavailable</div>
                    )}
                    <span className="vp-caption">OD Model Attention (Grad-CAM)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Section 4: Bilateral Findings & Quality Parameters */}
          <div className="doc-section">
            <div className="sec-header">3. BILATERAL RETINAL FINDINGS & QUALITY PARAMETERS</div>
            <table className="doc-table">
              <thead>
                <tr>
                  <th>CLINICAL PARAMETER</th>
                  <th>LEFT EYE (OS)</th>
                  <th>RIGHT EYE (OD)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Image Quality & Focus</td>
                  <td>{leftEye.quality ? `${leftEye.quality.focus.status} (${leftEye.quality.focus.score ? leftEye.quality.focus.score.toFixed(1) : '—'})` : '—'}</td>
                  <td>{rightEye.quality ? `${rightEye.quality.focus.status} (${rightEye.quality.focus.score ? rightEye.quality.focus.score.toFixed(1) : '—'})` : '—'}</td>
                </tr>
                <tr>
                  <td>Microaneurysms Detected</td>
                  <td>{leftEye.evidence?.microaneurysms ? `${leftEye.evidence.microaneurysms.count} count` : 'None'}</td>
                  <td>{rightEye.evidence?.microaneurysms ? `${rightEye.evidence.microaneurysms.count} count` : 'None'}</td>
                </tr>
                <tr>
                  <td>Hemorrhages Detected</td>
                  <td>{leftEye.evidence?.hemorrhages ? `${leftEye.evidence.hemorrhages.count} count` : 'None'}</td>
                  <td>{rightEye.evidence?.hemorrhages ? `${rightEye.evidence.hemorrhages.count} count` : 'None'}</td>
                </tr>
                <tr>
                  <td>Exudates Detected</td>
                  <td>{leftEye.evidence?.exudates ? `${leftEye.evidence.exudates.count} count` : 'None'}</td>
                  <td>{rightEye.evidence?.exudates ? `${rightEye.evidence.exudates.count} count` : 'None'}</td>
                </tr>
                <tr>
                  <td>Macular Involvement</td>
                  <td>{leftEye.evidence?.macularInvolvement ? 'Yes' : 'No'}</td>
                  <td>{rightEye.evidence?.macularInvolvement ? 'Yes' : 'No'}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Section 5: Reviewing Ophthalmologist Verification & Signature Block */}
          <div className="doc-section page-break-inside-avoid">
            <div className="sec-header">4. REVIEWING OPHTHALMOLOGIST VERIFICATION</div>
            <div className="ophthalmologist-review-box">
              <div className="ophth-grid">
                <div>
                  <span className="lbl">Reviewer Name:</span>
                  <span className="val">{exam.clinicalReview.reviewerName} (Ophthalmologist)</span>
                </div>
                <div>
                  <span className="lbl">Verified Grade:</span>
                  <span className="val font-bold">{verifiedGradeLabel}</span>
                </div>
                <div>
                  <span className="lbl">Verified Referable Status:</span>
                  <span className="val">
                    {exam.clinicalReview.clinicalReferable === null
                      ? 'Pending Review'
                      : exam.clinicalReview.clinicalReferable
                      ? 'Yes (Referral Required)'
                      : 'No (Non-Referable)'}
                  </span>
                </div>
              </div>

              <div className="ophth-notes-box">
                <span className="lbl">Clinical Impression & Follow-up Rationale:</span>
                <p className="notes-text">
                  {exam.clinicalReview.clinicalNotes || 'No additional clinical remarks recorded by reviewer.'}
                </p>
              </div>

              <div className="ophth-signature-row">
                <div className="digital-stamp">
                  <ShieldCheck size={16} className="text-blue-700" />
                  <div>
                    <div className="stamp-title">DIGITALLY VERIFIED CLINICAL AUDIT RECORD</div>
                    <div className="stamp-sub">Audit Trail ID: {exam.clinicalReview.auditTrailId || `AUDIT-${exam.id}`} • Timestamp: {exam.clinicalReview.savedAt || exam.timestamp}</div>
                  </div>
                </div>

                <div className="signature-line-box">
                  <div className="sig-line" />
                  <div className="sig-name">{exam.clinicalReview.reviewerName}</div>
                  <div className="sig-title">Consultant Ophthalmologist</div>
                </div>
              </div>
            </div>
          </div>

          {/* Mandatory Clinical Disclaimer Footer */}
          <div className="doc-disclaimer-bar">
            <AlertCircle size={14} className="flex-shrink-0" />
            <span>
              <strong>Regulatory & Clinical Disclaimer:</strong> AI-assisted diagnostic screening prototype (SIH26038). This document provides automated screening assistance and clinician review recording. Not a standalone definitive diagnosis. Final therapeutic decisions must be validated by a licensed medical practitioner.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

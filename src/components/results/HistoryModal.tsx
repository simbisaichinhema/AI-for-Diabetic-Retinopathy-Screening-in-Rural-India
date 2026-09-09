/**
 * INFINITE LOOPS — SIH26038
 * Longitudinal Patient History Modal
 */

import React from 'react';
import { X, Calendar } from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

export const HistoryModal: React.FC = () => {
  const { exam, isHistoryModalOpen, setIsHistoryModalOpen } = useScreening();

  if (!isHistoryModalOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.55)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      backdropFilter: 'blur(2px)',
    }}>
      <div style={{
        backgroundColor: '#ffffff',
        borderRadius: 10,
        width: '90%',
        maxWidth: 680,
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2)',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: '#fafbfc',
        }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
              Longitudinal Screening History
            </h2>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Patient: {exam.patient.name} ({exam.patient.id}) • Age: {exam.patient.age}
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsHistoryModalOpen(false)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Content */}
        <div style={{ padding: 20, maxHeight: '65vh', overflowY: 'auto' }}>
          {exam.previousExams.length > 0 && (
            <div style={{ padding: '9px 12px', marginBottom: 14, borderRadius: 6, background: '#fff7ed', border: '1px solid #fed7aa', color: '#9a3412', fontSize: 11, fontWeight: 700 }}>
              DEMO DATA — synthetic longitudinal examples for presentation only. These records are not clinical history.
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {/* Current Exam */}
            <div style={{
              padding: 14,
              borderRadius: 6,
              border: '1px solid var(--primary-blue-border)',
              backgroundColor: 'var(--primary-blue-light)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary-blue)', textTransform: 'uppercase' }}>
                  CURRENT EXAM — {exam.timestamp}
                </span>
                <span className={`badge ${exam.overallReferable ? 'badge-error' : 'badge-success'}`}>
                  {exam.overallGrade !== null ? `Grade ${exam.overallGrade}` : 'Pending'}
                </span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                {exam.overallGrade === 0 ? 'No Diabetic Retinopathy' :
                 exam.overallGrade === 2 ? 'Moderate Non-Proliferative DR' : 'Screening Complete'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                Reviewer: {exam.clinicalReview.reviewerName} • Status: {exam.clinicalReview.savedAt ? 'Clinician Verified' : 'AI Draft'}
              </div>
            </div>

            {/* Previous Historical Exams */}
            {exam.previousExams.map((prev) => (
              <div
                key={prev.id}
                style={{
                  padding: 14,
                  borderRadius: 6,
                  border: '1px solid var(--border-subtle)',
                  backgroundColor: '#ffffff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>
                    <Calendar size={13} style={{ color: 'var(--text-muted)' }} />
                    <span>{prev.date}</span>
                  </div>
                  <span className={`badge ${prev.isReferable ? 'badge-error' : 'badge-neutral'}`}>
                    {prev.gradeLabel}
                  </span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                  Reviewing Clinician: {prev.reviewerName}
                </div>
                {prev.notes && (
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, fontStyle: 'italic' }}>
                    "{prev.notes}"
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '12px 20px',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          justifyContent: 'flex-end',
          backgroundColor: '#fafbfc',
        }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => setIsHistoryModalOpen(false)}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

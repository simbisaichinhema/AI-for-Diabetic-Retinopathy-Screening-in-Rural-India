/**
 * INFINITE LOOPS — SIH26038
 * Session Start · 3-Stage Sliding Flow
 *   Stage 0 IDLE          → Retinal fundus hero bg + single CTA
 *   Stage 1 ENTER_ID      → Aadhaar input panel slides up
 *   Stage 2 PATIENT_FOUND → Profile card slides in from right
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  ArrowRight,
  User,
  CheckCircle,
  CreditCard,
  MapPin,
  ChevronLeft,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';
import { Patient, PreviousExam } from '../../types/clinical';
import { createInitialExamination } from '../../services/clinicalDefaults';

type Stage = 'idle' | 'enter_id' | 'patient_found';

interface PatientRecord {
  aadhaar: string;
  abhaId: string;
  name: string;
  age: number;
  sex: 'Male' | 'Female' | 'Other';
  location: string;
  diabetesInfo: string;
  riskLevel: 'HIGH' | 'MODERATE' | 'LOW';
}

const CITIZEN_DB: Record<string, PatientRecord> = {
  '543289012345': {
    aadhaar: '5432 8901 2345',
    abhaId: 'ABHA-91-4820-1928',
    name: 'Ramesh Kumar Verma',
    age: 58,
    sex: 'Male',
    location: 'Shivpuri, Madhya Pradesh',
    diabetesInfo: 'Type 2 Diabetes · 8 Years',
    riskLevel: 'HIGH',
  },
  '789012345678': {
    aadhaar: '7890 1234 5678',
    abhaId: 'ABHA-91-3312-8874',
    name: 'Sunita Devi Sharma',
    age: 52,
    sex: 'Female',
    location: 'Bhind, Madhya Pradesh',
    diabetesInfo: 'Type 2 Diabetes · 4 Years',
    riskLevel: 'MODERATE',
  },
  '901234567890': {
    aadhaar: '9012 3456 7890',
    abhaId: 'ABHA-91-7761-4509',
    name: 'Anil Narayan Patil',
    age: 44,
    sex: 'Male',
    location: 'Chhindwara, Madhya Pradesh',
    diabetesInfo: 'Type 2 Diabetes · 1 Year',
    riskLevel: 'LOW',
  },
};

const fmt = (val: string) => {
  const d = val.replace(/\D/g, '').slice(0, 12);
  return d.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
};

const riskColor = (r: PatientRecord['riskLevel']) =>
  r === 'HIGH' ? '#ef4444' : r === 'MODERATE' ? '#f59e0b' : '#10b981';

const DEMO_HISTORY: Record<string, PreviousExam[]> = {
  '543289012345': [
    { id: 'DEMO-5432-01', date: '12 Jan 2024', grade: 0, gradeLabel: 'Grade 0 — No DR', isReferable: false, reviewerName: 'Demo record', notes: 'Synthetic baseline for demonstration.' },
    { id: 'DEMO-5432-02', date: '18 Aug 2024', grade: 1, gradeLabel: 'Grade 1 — Mild DR', isReferable: false, reviewerName: 'Demo record', notes: 'Synthetic progression example.' },
  ],
  '789012345678': [
    { id: 'DEMO-7890-01', date: '03 Mar 2024', grade: 0, gradeLabel: 'Grade 0 — No DR', isReferable: false, reviewerName: 'Demo record', notes: 'Synthetic baseline for demonstration.' },
    { id: 'DEMO-7890-02', date: '22 Nov 2024', grade: 1, gradeLabel: 'Grade 1 — Mild DR', isReferable: false, reviewerName: 'Demo record', notes: 'Synthetic monitoring example.' },
  ],
  '901234567890': [
    { id: 'DEMO-9012-01', date: '09 May 2024', grade: 0, gradeLabel: 'Grade 0 — No DR', isReferable: false, reviewerName: 'Demo record', notes: 'Synthetic baseline for demonstration.' },
  ],
};

export const SessionStartPage: React.FC = () => {
  const { navigateToStep, setExam } = useScreening();

  const [stage, setStage] = useState<Stage>('idle');
  const [raw, setRaw] = useState('');
  const [patient, setPatient] = useState<PatientRecord | null>(null);
  const [searching, setSearching] = useState(false);
  const [notFound, setNotFound] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (stage === 'enter_id') setTimeout(() => inputRef.current?.focus(), 420);
  }, [stage]);

  const lookup = (clean: string) => {
    setSearching(true);
    setNotFound(false);
    setTimeout(() => {
      setSearching(false);
      if (CITIZEN_DB[clean]) {
        setPatient(CITIZEN_DB[clean]);
        setStage('patient_found');
      } else {
        setNotFound(true);
        setPatient(null);
        setStage('enter_id');
      }
    }, 650);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '').slice(0, 12);
    setRaw(val);
    setNotFound(false);
    if (val.length === 12) lookup(val);
    else { setPatient(null); if (stage === 'patient_found') setStage('enter_id'); }
  };

  const handlePreset = (key: string) => { setRaw(key); lookup(key); };

  const handleBegin = () => {
    if (!patient) return;
    const p: Patient = {
      id: patient.abhaId, name: patient.name,
      age: patient.age, sex: patient.sex,
      villageOrDistrict: patient.location,
    };
    const nextExam = createInitialExamination(p);
    nextExam.previousExams = DEMO_HISTORY[patient.aadhaar.replace(/\s/g, '')] || [];
    setExam(nextExam);
    navigateToStep('acquisition');
  };

  return (
    <div className="ss-root">

      {/* ── HEADER ── */}
      <header className="ss-header">
        <div className="ss-header-inner">
          <img src="/assets/sih_logo_bar.jpg" alt="SIH 2026" className="ss-logo" />
          <div className="ss-header-right">
            <span className="ss-project-id">SIH26038</span>
            <span className="ss-divider">·</span>
            <span className="ss-team">INFINITE LOOPS</span>
            <span className="ss-divider">·</span>
            <span className="ss-proto-badge">PROTOTYPE</span>
          </div>
        </div>
      </header>

      {/* ── STAGE CONTAINER ── */}
      <main className="ss-main">

        {/* ═══ STAGE 0 — HERO (Side-by-side Layout) ═══ */}
        <div className={`ss-stage ss-stage-idle ${stage === 'idle' ? 'stage-active' : 'stage-exit'}`}>
          <div className="ss-hero-eye-background" aria-hidden="true">
            <img src="/assets/head_reference_left.jpg" alt="" />
            <img src="/assets/head_reference_right.jpg" alt="" />
          </div>
          <div className="ss-hero-grid">
            
            {/* Left Column: Circular Fundus Graphic with Target Marker */}
            <div className="ss-hero-graphic">
              <div className="ss-fundus-frame">
                <img
                  src="/assets/fundus_bg.png"
                  alt="Retinal Fundus Examination"
                  className="ss-fundus-circle"
                  draggable={false}
                />
                {/* Yellow AI detection indicator target ring */}
                <div className="ss-target-ring" />
              </div>
            </div>

            {/* Right Column: Title & Action CTA */}
            <div className="ss-hero-text-block">
              <div className="ss-hero-label">
                <span className="ss-pulse-dot" />
                AI-Powered Retinal Screening · NHM India
              </div>

              <h1 className="ss-hero-title">
                Diabetic Retinopathy<br />
                <span className="ss-hero-title-accent">Detection System</span>
              </h1>

              <p className="ss-hero-sub">
                Smart India Hackathon 2026 · Problem SIH26038
              </p>

              <div className="ss-learning-note">
                <span className="ss-learning-dot" />
                HUMAN-VALIDATED MODEL IMPROVEMENT LOOP
              </div>

              <button
                id="btn-start-session"
                className="ss-btn-hero"
                onClick={() => { setStage('enter_id'); setRaw(''); setPatient(null); setNotFound(false); }}
              >
                <span>Start Screening Session</span>
                <ArrowRight size={20} />
              </button>
            </div>

          </div>
        </div>

        {/* ═══ STAGES 1 + 2 — INTAKE ═══ */}
        <div className={`ss-stage ss-stage-intake ${stage !== 'idle' ? 'stage-active' : 'stage-hidden'}`}>
          <div className="ss-intake-shell">

            {/* ── LEFT: Aadhaar Input Panel ── */}
            <div className={`ss-input-panel ${stage !== 'idle' ? 'panel-enter' : ''}`}>

              <button className="ss-back-btn" onClick={() => setStage('idle')}>
                <ChevronLeft size={16} /> Back
              </button>

              <div className="ss-input-heading">
                <CreditCard size={22} className="ss-input-heading-icon" />
                <div>
                  <h2 className="ss-input-title">Patient Identification</h2>
                  <p className="ss-input-sub">Enter 12-digit Aadhaar number</p>
                </div>
              </div>

              {/* Quick presets */}
              <div className="ss-presets">
                <span className="ss-presets-label">Test Citizens</span>
                <div className="ss-preset-chips">
                  {Object.entries(CITIZEN_DB).map(([key, rec]) => (
                    <button
                      key={key}
                      className={`ss-chip ${raw === key ? 'chip-sel' : ''}`}
                      onClick={() => handlePreset(key)}
                    >
                      {rec.name.split(' ')[0]} · {rec.age}y {rec.sex[0]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Input field */}
              <div className="ss-field-wrap">
                <div className={`ss-field-box ${searching ? 'field-searching' : ''} ${patient ? 'field-ok' : ''} ${notFound ? 'field-error' : ''}`}>
                  <CreditCard size={18} className="ss-field-icon" />
                  <input
                    ref={inputRef}
                    id="aadhaar-input"
                    type="text"
                    className="ss-aadhaar-input"
                    placeholder="XXXX  XXXX  XXXX"
                    value={fmt(raw)}
                    onChange={handleChange}
                    maxLength={14}
                  />
                  <div className="ss-field-status">
                    {searching && <div className="ss-spinner" />}
                    {patient && !searching && <CheckCircle size={18} className="ss-icon-ok" />}
                  </div>
                </div>
                {notFound && <p className="ss-field-msg error">No record found in national database</p>}
                {patient && !searching && <p className="ss-field-msg ok"><CheckCircle size={12} /> Patient verified</p>}
              </div>
            </div>

            {/* ── RIGHT: Patient Profile Card (Stage 2) OR System Verification Info (Stage 1) ── */}
            <div className="ss-profile-panel">
              {stage === 'patient_found' && patient ? (
                <div className="ss-profile-card panel-enter">

                  {/* Avatar */}
                  <div className="ss-avatar-wrap">
                    <div className="ss-avatar">
                      <User size={40} strokeWidth={1.5} />
                    </div>
                    <div className="ss-risk-dot" style={{ background: riskColor(patient.riskLevel) }} />
                  </div>

                  {/* Name */}
                  <div className="ss-profile-name-block">
                    <h3 className="ss-profile-name">{patient.name}</h3>
                    <div className="ss-profile-demo">
                      <span>{patient.age} yrs</span>
                      <span className="dot">·</span>
                      <span>{patient.sex}</span>
                    </div>
                  </div>

                  {/* Info rows */}
                  <div className="ss-profile-info">
                    <div className="ss-info-row">
                      <span className="info-k">ABHA ID</span>
                      <span className="info-v mono">{patient.abhaId}</span>
                    </div>
                    <div className="ss-info-row">
                      <span className="info-k"><MapPin size={12} /> Location</span>
                      <span className="info-v">{patient.location}</span>
                    </div>
                  </div>

                  {/* Verified */}
                  <div className="ss-verified-bar">
                    <CheckCircle size={14} className="ss-verified-icon" />
                    <span>National Health Database Verified</span>
                  </div>

                  {/* Begin CTA */}
                  <button id="btn-begin-screening" className="ss-btn-begin" onClick={handleBegin}>
                    <span>Begin Retinal Screening</span>
                    <ArrowRight size={20} />
                  </button>
                </div>
              ) : (
                /* Stage 1 neutral profile placeholder */
                <div className="ss-info-helper-card panel-enter">
                  <div className="ss-patient-placeholder">
                    <img src="/assets/patient_placeholder.svg" alt="Sample patient profile" />
                    <span><User size={13} /> SAMPLE PATIENT</span>
                  </div>
                  <h3 className="ss-helper-title">Patient profile preview</h3>
                  <p className="ss-helper-sub">Verified patient details and bilateral eye records will appear here.</p>
                </div>
              )}
            </div>

          </div>
        </div>

      </main>

      {/* ── FOOTER ── */}
      <footer className="ss-footer">
        Smart India Hackathon 2026 · Problem SIH26038 · Team INFINITE LOOPS · Prototype
      </footer>
    </div>
  );
};

/**
 * INFINITE LOOPS — SIH26038
 * Clinical State Defaults & Examination Initializers
 * Real empty states without hardcoded mock patient data.
 */

import { Examination, EyeData, EyeSide, Patient } from '../types/clinical';

export const INITIAL_PATIENT: Patient = {
  id: '',
  name: '',
  age: 0,
  sex: 'Male',
  villageOrDistrict: '',
};

/**
 * Creates an empty examination state for a new screening session
 */
export function createInitialExamination(patient: Patient = INITIAL_PATIENT): Examination {
  const initialEye = (side: EyeSide): EyeData => ({
    side,
    sideLabel: side === 'OS' ? 'Left Eye (OS)' : 'Right Eye (OD)',
    imageSrc: null,
    acquisitionMethod: 'upload',
    quality: null,
    predictionGrade: null,
    confidence: null,
    probabilities: null,
    isReferable: null,
    evidence: null,
    gradCamSrc: null,
    gradCamAvailable: false,
    enhancedSrc: null,
    enhancedAvailable: false,
  });

  const now = new Date();
  const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return {
    id: `EXAM-${Date.now().toString().slice(-6)}`,
    patient,
    timestamp: `${dateStr}, ${timeStr}`,
    modelVersion: 'DR-EfficientNetB0',
    status: 'draft',
    leftEye: initialEye('OS'),
    rightEye: initialEye('OD'),
    overallGrade: null,
    overallConfidence: null,
    overallReferable: null,
    referableProbability: null,
    aiRecommendation: 'Pending screening analysis',
    keyInsights: [],
    clinicalReview: {
      reviewerName: 'Dr. Sharma',
      reviewerRole: 'Ophthalmologist',
      clinicalGrade: null,
      clinicalReferable: null,
      clinicalNotes: '',
      savedAt: null,
    },
    previousExams: [],
  };
}

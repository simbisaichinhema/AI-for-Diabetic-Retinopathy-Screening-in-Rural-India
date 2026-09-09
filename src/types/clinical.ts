/**
 * INFINITE LOOPS — SIH26038
 * Clinical Data Types & Schemas
 */

export type EyeSide = 'OS' | 'OD'; // OS = Left Eye (Oculus Sinister), OD = Right Eye (Oculus Dexter)

export type DRGradeIndex = 0 | 1 | 2 | 3 | 4;

export interface DRGradeInfo {
  grade: DRGradeIndex;
  label: string;
  shortLabel: string;
  description: string;
  isReferable: boolean;
}

export const DR_GRADES: Record<DRGradeIndex, DRGradeInfo> = {
  0: {
    grade: 0,
    label: 'Grade 0 — No Diabetic Retinopathy',
    shortLabel: 'No DR',
    description: 'No microaneurysms, hemorrhages, or retinal abnormalities visible.',
    isReferable: false,
  },
  1: {
    grade: 1,
    label: 'Grade 1 — Mild Non-Proliferative DR',
    shortLabel: 'Mild DR',
    description: 'Microaneurysms only. Early disease stage; routine annual follow-up recommended.',
    isReferable: false,
  },
  2: {
    grade: 2,
    label: 'Grade 2 — Moderate Non-Proliferative DR',
    shortLabel: 'Moderate DR',
    description: 'More than microaneurysms, but less than severe NPDR. Referable for ophthalmological care.',
    isReferable: true,
  },
  3: {
    grade: 3,
    label: 'Grade 3 — Severe Non-Proliferative DR',
    shortLabel: 'Severe DR',
    description: 'High risk of progression to PDR. Rule 4-2-1 criteria met. Prompt ophthalmologist referral required.',
    isReferable: true,
  },
  4: {
    grade: 4,
    label: 'Grade 4 — Proliferative DR',
    shortLabel: 'Proliferative DR',
    description: 'Neovascularization, vitreous/preretinal hemorrhage. Urgent referral required.',
    isReferable: true,
  },
};

export type QualityLevel = 'Good' | 'Acceptable' | 'Borderline' | 'Insufficient' | 'Poor';
export type QualityDecision = 'ACCEPTED' | 'REJECTED' | 'PENDING';

export interface ImageQualityMetrics {
  focus: {
    status: QualityLevel;
    score?: number; // e.g., Laplacian variance (312.5)
    details?: string;
  };
  illumination: {
    status: QualityLevel;
    score?: number; // e.g., brightness mean (125.3)
    details?: string;
  };
  fieldOfView: {
    status: QualityLevel;
    details: string; // e.g. 'Optic disc and macula visible'
  };
  fundusValidity: {
    isValid: boolean;
    details: string; // e.g. 'Valid retinal fundus photograph'
  };
  artifacts?: {
    status: 'None' | 'Minimal' | 'Significant';
    details?: string;
  };
  overallStatus: QualityDecision;
  failureReasons?: string[]; // Populated if REJECTED
}

export interface DRProbabilityDistribution {
  grade0: number; // 0.0 - 1.0 (e.g. 0.443)
  grade1: number;
  grade2: number;
  grade3: number;
  grade4: number;
}

export interface RetinalEvidence {
  microaneurysms?: { count: number; confidence: number } | null;
  hemorrhages?: { count: number; confidence: number } | null;
  exudates?: { count: number; confidence: number } | null;
  cottonWoolSpots?: { count: number; confidence: number } | null;
  vesselAbnormalities?: 'None' | 'Mild' | 'Moderate' | 'Severe' | 'Not available';
  macularInvolvement?: boolean | null;
  statusNote?: string; // e.g. 'Module pending integration' or 'AI Detected'
}

export interface EyeData {
  side: EyeSide;
  sideLabel: string; // 'Left Eye (OS)' or 'Right Eye (OD)'
  imageSrc: string | null;
  fileName?: string;
  fileSize?: number;
  capturedAt?: string;
  acquisitionMethod: 'upload' | 'device_capture';
  
  // Quality Check
  quality: ImageQualityMetrics | null;
  
  // AI Inference (from backend / model)
  predictionGrade: DRGradeIndex | null;
  confidence: number | null; // 0.0 - 1.0
  probabilities: DRProbabilityDistribution | null;
  isReferable: boolean | null;
  
  // Evidence & Explainability
  evidence: RetinalEvidence | null;
  gradCamSrc: string | null; // Heatmap or attribution image, null if unavailable
  gradCamAvailable: boolean;
  enhancedSrc: string | null; // Contrast/vessel enhanced image
  enhancedAvailable: boolean;
}

export interface Patient {
  id: string;
  name: string;
  age: number;
  sex: 'Male' | 'Female' | 'Other';
  villageOrDistrict?: string;
  diabetesDurationYears?: number;
  contactNumber?: string;
}

export interface PreviousExam {
  id: string;
  date: string;
  grade: DRGradeIndex;
  gradeLabel: string;
  isReferable: boolean;
  reviewerName: string;
  notes?: string;
}

export interface ClinicalReview {
  reviewerName: string;
  reviewerRole: string; // e.g., 'Ophthalmologist'
  clinicalGrade: DRGradeIndex | null;
  clinicalReferable: boolean | null;
  clinicalNotes: string;
  savedAt: string | null;
  auditTrailId?: string;
}

export interface Examination {
  id: string;
  patient: Patient;
  timestamp: string;
  modelVersion: string;
  status: 'draft' | 'quality_check' | 'analysing' | 'completed' | 'reviewed';
  
  // Bilateral Eyes
  leftEye: EyeData;
  rightEye: EyeData;
  
  // Bilateral Summary AI Assessment
  overallGrade: DRGradeIndex | null;
  overallConfidence: number | null;
  overallReferable: boolean | null;
  referableProbability: number | null;
  aiRecommendation: string;
  keyInsights: string[];
  
  // Clinical Review (preserved separately from AI assessment)
  clinicalReview: ClinicalReview;
  
  // Longitudinal Comparison
  previousExams: PreviousExam[];
}

export type ScreeningStep = 
  | 'session_start'
  | 'acquisition'
  | 'quality_processing'
  | 'quality_results'
  | 'analysis_processing'
  | 'clinical_results';

export interface QualityCheckStage {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}

export interface AnalysisStage {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progressPercentage?: number;
}

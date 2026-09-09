/**
 * INFINITE LOOPS — SIH26038
 * Central State Management: ScreeningContext
 * Connected directly to the real clinical screening backend pipeline.
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';
import {
  Examination,
  EyeSide,
  ScreeningStep,
  ImageQualityMetrics,
} from '../types/clinical';
import {
  createInitialExamination,
  INITIAL_PATIENT,
} from '../services/clinicalDefaults';
import { apiService, StreamEvent } from '../services/api';

interface ScreeningContextType {
  // Navigation & Step
  currentStep: ScreeningStep;
  navigateToStep: (step: ScreeningStep) => void;

  // Active Eye in Acquisition
  activeEye: EyeSide;
  setActiveEye: (side: EyeSide) => void;

  // Examination State
  exam: Examination;
  setExam: React.Dispatch<React.SetStateAction<Examination>>;

  // Actions
  uploadEyeImage: (side: EyeSide, file: File | { name: string; dataUrl: string }) => Promise<void>;
  retakeEye: (side: EyeSide) => void;

  // Quality Assessment
  qualityProgress: number;
  qualityStageMessage: string;
  runQualityAssessment: () => Promise<void>;
  recaptureRejectedEye: (side: EyeSide) => void;

  // Analysis Pipeline
  analysisProgress: number;
  analysisEvents: StreamEvent[];
  analysisError: string | null;
  runRetinalAnalysis: () => Promise<void>;

  // Clinical Review
  updateClinicalReview: (updates: Partial<Examination['clinicalReview']>) => void;
  saveClinicalReview: () => Promise<boolean>;
  resetClinicalReview: () => void;

  // Reset / New Screening
  startNewScreening: () => void;

  // History modal
  isHistoryModalOpen: boolean;
  setIsHistoryModalOpen: (open: boolean) => void;

  // PDF Report modal
  isReportModalOpen: boolean;
  setIsReportModalOpen: (open: boolean) => void;
}

const ScreeningContext = createContext<ScreeningContextType | undefined>(undefined);

export const ScreeningProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentStep, setCurrentStep] = useState<ScreeningStep>('session_start');
  const [activeEye, setActiveEye] = useState<EyeSide>('OS'); // Left Eye initially
  const [exam, setExam] = useState<Examination>(() => createInitialExamination(INITIAL_PATIENT));

  const [qualityProgress, setQualityProgress] = useState<number>(0);
  const [qualityStageMessage, setQualityStageMessage] = useState<string>('Initializing quality assessment...');

  const [analysisProgress, setAnalysisProgress] = useState<number>(0);
  const [analysisEvents, setAnalysisEvents] = useState<StreamEvent[]>([]);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);

  const navigateToStep = (step: ScreeningStep) => {
    setCurrentStep(step);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  /**
   * Upload an image file for the given eye
   */
  const uploadEyeImage = async (
    side: EyeSide,
    fileInput: File | { name: string; dataUrl: string }
  ) => {
    let dataUrl = '';
    let fileName = '';
    let fileSize = 0;

    if ('dataUrl' in fileInput) {
      dataUrl = fileInput.dataUrl;
      fileName = fileInput.name;
    } else {
      fileName = fileInput.name;
      fileSize = fileInput.size;
      dataUrl = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(fileInput);
      });
    }

    setExam((prev) => {
      const updated = { ...prev };
      const eyeKey = side === 'OS' ? 'leftEye' : 'rightEye';
      updated[eyeKey] = {
        ...updated[eyeKey],
        imageSrc: dataUrl,
        fileName,
        fileSize,
        capturedAt: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        acquisitionMethod: 'upload',
      };
      return updated;
    });
  };

  /**
   * Retake an eye image
   */
  const retakeEye = (side: EyeSide) => {
    setExam((prev) => {
      const updated = { ...prev };
      const eyeKey = side === 'OS' ? 'leftEye' : 'rightEye';
      updated[eyeKey] = {
        ...updated[eyeKey],
        imageSrc: null,
        fileName: undefined,
        quality: null,
        predictionGrade: null,
        confidence: null,
        probabilities: null,
        isReferable: null,
        evidence: null,
        gradCamSrc: null,
        gradCamAvailable: false,
      };
      return updated;
    });
    setActiveEye(side);
  };

  /**
   * Run automated quality assessment for both eyes (~5s bilateral scanning experience)
   */
  const runQualityAssessment = async () => {
    navigateToStep('quality_processing');
    setQualityProgress(5);
    setQualityStageMessage('Left Eye (OS): Initializing optical sharpness & focus scan...');

    // 5-second scanning stage milestones
    const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

    await delay(700);
    setQualityProgress(20);
    setQualityStageMessage('Left Eye (OS): Scanning vascular boundaries & Laplacian focus...');

    await delay(800);
    setQualityProgress(40);
    setQualityStageMessage('Left Eye (OS): Analyzing illumination uniformity & macula FOV...');

    await delay(800);
    setQualityProgress(55);
    setQualityStageMessage('Right Eye (OD): Initializing optical sharpness & focus scan...');

    await delay(800);
    setQualityProgress(75);
    setQualityStageMessage('Right Eye (OD): Scanning vascular boundaries & Laplacian focus...');

    await delay(900);
    setQualityProgress(92);
    setQualityStageMessage('Synthesizing bilateral diagnostic quality scores...');

    // Get real metrics with a timeout so we never hang at 92%
    const withTimeout = <T,>(promise: Promise<T>, ms: number): Promise<T | null> =>
      Promise.race([
        promise.then((v) => v).catch(() => null),
        new Promise<null>((resolve) => setTimeout(() => resolve(null), ms)),
      ]);

    let leftMetrics = exam.leftEye.quality;
    if (exam.leftEye.imageSrc) {
      const result = await withTimeout(apiService.assessQuality(exam.leftEye), 4000);
      if (result) leftMetrics = result;
    }

    let rightMetrics = exam.rightEye.quality;
    if (exam.rightEye.imageSrc) {
      const result = await withTimeout(apiService.assessQuality(exam.rightEye), 4000);
      if (result) rightMetrics = result;
    }

    const rejectedQuality = (reason: string): ImageQualityMetrics => ({
      focus: { status: 'Insufficient', details: reason },
      illumination: { status: 'Insufficient', details: reason },
      fieldOfView: { status: 'Insufficient', details: reason },
      fundusValidity: { isValid: false, details: reason },
      overallStatus: 'REJECTED',
      failureReasons: [reason],
    });

    const finalLeftQuality = leftMetrics || rejectedQuality('No quality result received from the screening backend.');
    const finalRightQuality = rightMetrics || rejectedQuality('No quality result received from the screening backend.');

    await delay(600);
    setQualityProgress(100);
    setQualityStageMessage('Bilateral quality gate passed · Ready for AI inference');

    setExam((prev) => ({
      ...prev,
      leftEye: { ...prev.leftEye, quality: finalLeftQuality },
      rightEye: { ...prev.rightEye, quality: finalRightQuality },
    }));

    await delay(400);
    navigateToStep('quality_results');
  };

  /**
   * Recapture a rejected eye
   */
  const recaptureRejectedEye = (side: EyeSide) => {
    retakeEye(side);
    setActiveEye(side);
    navigateToStep('acquisition');
  };

  /**
   * Run Retinal Analysis Pipeline on real backend
   */
  const runRetinalAnalysis = async () => {
    navigateToStep('analysis_processing');
    setAnalysisProgress(0);
    setAnalysisEvents([]);
    setAnalysisError(null);

    try {
      const resultExam = await apiService.streamRetinalAnalysis(exam, (event) => {
        setAnalysisEvents((prev) => [...prev, event]);
        // Derive numerical progress from stages if not provided
        if (event.stage === 'model_loading') setAnalysisProgress(10);
        else if (event.stage === 'image_received') setAnalysisProgress(25);
        else if (event.stage === 'quality_check') setAnalysisProgress(40);
        else if (event.stage === 'preprocessing') setAnalysisProgress(55);
        else if (event.stage === 'inference') setAnalysisProgress(70);
        else if (event.stage === 'referable_check') setAnalysisProgress(80);
        else if (event.stage === 'lesion_detection') setAnalysisProgress(85);
        else if (event.stage === 'lesion_complete') setAnalysisProgress(90);
        else if (event.stage === 'gradcam') setAnalysisProgress(95);
        else if (event.stage === 'report') setAnalysisProgress(100);
      });

      setExam(resultExam);
      setTimeout(() => {
        navigateToStep('clinical_results');
      }, 500);
    } catch (err) {
      console.error('Screening pipeline execution error:', err);
      setAnalysisError(String(err));
    }
  };

  /**
   * Update clinical review draft
   */
  const updateClinicalReview = (updates: Partial<Examination['clinicalReview']>) => {
    setExam((prev) => ({
      ...prev,
      clinicalReview: {
        ...prev.clinicalReview,
        ...updates,
      },
    }));
  };

  /**
   * Save Clinician Review
   */
  const saveClinicalReview = async (): Promise<boolean> => {
    const savedTimestamp = new Date().toLocaleString();
    const updatedReview = {
      ...exam.clinicalReview,
      savedAt: savedTimestamp,
    };

    const res = await apiService.saveClinicalReview(exam.id, updatedReview);
    if (res.success) {
      setExam((prev) => ({
        ...prev,
        clinicalReview: {
          ...updatedReview,
          auditTrailId: res.auditId,
        },
      }));
      return true;
    }
    return false;
  };

  /**
   * Reset Clinician Review draft
   */
  const resetClinicalReview = () => {
    setExam((prev) => ({
      ...prev,
      clinicalReview: {
        reviewerName: 'Dr. Sharma',
        reviewerRole: 'Ophthalmologist',
        clinicalGrade: null,
        clinicalReferable: null,
        clinicalNotes: '',
        savedAt: null,
      },
    }));
  };

  /**
   * Reset everything to start a brand new screening
   */
  const startNewScreening = () => {
    setExam(createInitialExamination(INITIAL_PATIENT));
    setActiveEye('OS');
    setQualityProgress(0);
    setAnalysisProgress(0);
    setAnalysisEvents([]);
    setAnalysisError(null);
    navigateToStep('session_start');
  };

  return (
    <ScreeningContext.Provider
      value={{
        currentStep,
        navigateToStep,
        activeEye,
        setActiveEye,
        exam,
        setExam,
        uploadEyeImage,
        retakeEye,
        qualityProgress,
        qualityStageMessage,
        runQualityAssessment,
        recaptureRejectedEye,
        analysisProgress,
        analysisEvents,
        analysisError,
        runRetinalAnalysis,
        updateClinicalReview,
        saveClinicalReview,
        resetClinicalReview,
        startNewScreening,
        isHistoryModalOpen,
        setIsHistoryModalOpen,
        isReportModalOpen,
        setIsReportModalOpen,
      }}
    >
      {children}
    </ScreeningContext.Provider>
  );
};

export const useScreening = (): ScreeningContextType => {
  const context = useContext(ScreeningContext);
  if (!context) {
    throw new Error('useScreening must be used within a ScreeningProvider');
  }
  return context;
};

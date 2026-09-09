/**
 * INFINITE LOOPS — SIH26038
 * Central Clinical API Service & Adapter Layer
 * Connects directly to the real FastAPI backend for health, model status,
 * quality gate assessment, DR classification, Grad-CAM, and lesion analysis.
 */

import {
  Examination,
  EyeData,
  ImageQualityMetrics,
  DRGradeIndex,
  RetinalEvidence,
  DRProbabilityDistribution,
} from '../types/clinical';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export interface StreamEvent {
  stage: 'model_loading' | 'image_received' | 'quality_check' | 'preprocessing' | 'inference' | 'referable_check' | 'lesion_detection' | 'lesion_complete' | 'gradcam' | 'report';
  name: string;
  message: string;
  data?: unknown;
}

export interface BackendHealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface ModelStatusResponse {
  warming: boolean;
  fallback: boolean;
  error: string;
  models: {
    classifier: boolean;
  };
}

export interface BackendQualityResponse {
  usable: boolean;
  focus: number;
  illumination: number;
  field_of_view: number;
  overall: number;
}

export interface BackendScreenResponse {
  case_id: string;
  status: 'completed' | 'recapture_required' | 'error';
  quality?: BackendQualityResponse;
  dr_prediction?: {
    grade: number;
    label: string;
    confidence: number;
    probabilities: Record<string, number>;
  };
  referable_dr?: {
    is_referable: boolean;
    probability: number;
    definition: string;
  };
  lesions?: {
    microaneurysms?: { detected: boolean; count: number; confidence?: number; locations?: number[][] };
    hemorrhages?: { detected: boolean; count: number; confidence?: number; locations?: number[][] };
    exudates?: { detected: boolean; count: number; confidence?: number; locations?: number[][] };
    vessels?: { mean_width?: number; vessel_density?: number; quality?: string; status?: string };
  };
  gradcam_image?: string | null;
  enhanced_image?: string | null;
  report?: Record<string, unknown>;
  message?: string;
}

/**
 * Convert base64 data URL to Blob
 */
export function dataUrlToBlob(dataUrl: string): Blob {
  const arr = dataUrl.split(',');
  const mimeMatch = arr[0].match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : 'image/jpeg';
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}

export class ClinicalApiService {
  private static instance: ClinicalApiService;

  public static getInstance(): ClinicalApiService {
    if (!ClinicalApiService.instance) {
      ClinicalApiService.instance = new ClinicalApiService();
    }
    return ClinicalApiService.instance;
  }

  /**
   * Check backend health (GET /api/health)
   */
  async checkHealth(): Promise<BackendHealthResponse> {
    try {
      const res = await fetch(`${BASE_URL}/api/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data: BackendHealthResponse = await res.json();
      return data;
    } catch {
      return {
        status: 'offline',
        version: '2.0.0',
        timestamp: new Date().toISOString(),
      };
    }
  }

  /**
   * Check model status (GET /api/models/status)
   */
  async getModelStatus(): Promise<ModelStatusResponse> {
    try {
      const res = await fetch(`${BASE_URL}/api/models/status`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      return await res.json();
    } catch (err) {
      return {
        warming: false,
        fallback: true,
        error: `Backend unreachable (${String(err)})`,
        models: { classifier: false },
      };
    }
  }

  /**
   * Map backend QualityResult to Frontend ImageQualityMetrics
   */
  mapQualityMetrics(quality?: BackendQualityResponse): ImageQualityMetrics {
    if (!quality) {
      return {
        focus: { status: 'Insufficient', details: 'No quality data received' },
        illumination: { status: 'Insufficient', details: 'No quality data received' },
        fieldOfView: { status: 'Insufficient', details: 'No quality data received' },
        fundusValidity: { isValid: false, details: 'Validation failed' },
        overallStatus: 'REJECTED',
        failureReasons: ['Quality assessment returned no valid metrics'],
      };
    }

    const focusPct = quality.focus * 100;
    const illumPct = quality.illumination * 100;
    const fovPct = quality.field_of_view * 100;
    const isUsable = quality.usable;

    const getStatus = (score: number) => {
      if (score >= 80) return 'Good';
      if (score >= 60) return 'Acceptable';
      if (score >= 40) return 'Borderline';
      return 'Insufficient';
    };

    const failureReasons: string[] = [];
    if (focusPct < 40) failureReasons.push(`Focus score low (${focusPct.toFixed(1)}%) — vessel edges unsharp`);
    if (illumPct < 40) failureReasons.push(`Illumination irregular (${illumPct.toFixed(1)}%) — uneven exposure`);
    if (fovPct < 40) failureReasons.push(`Field of View insufficient (${fovPct.toFixed(1)}%) — macula/disc not centered`);

    return {
      focus: {
        status: getStatus(focusPct),
        score: quality.focus * 400, // Normalized Laplacian representation
        details: `Focus confidence: ${focusPct.toFixed(1)}%`,
      },
      illumination: {
        status: getStatus(illumPct),
        score: quality.illumination * 255,
        details: `Illumination confidence: ${illumPct.toFixed(1)}%`,
      },
      fieldOfView: {
        status: getStatus(fovPct),
        details: `FOV score: ${fovPct.toFixed(1)}%`,
      },
      fundusValidity: {
        isValid: isUsable,
        details: isUsable ? 'Valid human retinal fundus' : 'Image failed clinical diagnostic threshold',
      },
      overallStatus: isUsable ? 'ACCEPTED' : 'REJECTED',
      failureReasons: failureReasons.length > 0 ? failureReasons : undefined,
    };
  }

  /**
   * Run real screening on a single eye image via POST /api/screen
   */
  async screenSingleEye(
    side: 'OS' | 'OD',
    imageSrc: string
  ): Promise<BackendScreenResponse> {
    const blob = dataUrlToBlob(imageSrc);
    const formData = new FormData();
    formData.append('file', blob, `${side}_fundus.jpg`);

    const res = await fetch(`${BASE_URL}/api/screen`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`Screening failed (HTTP ${res.status}): ${errorText}`);
    }

    return await res.json();
  }

  /**
   * Stream screening pipeline via POST /api/screen-stream (SSE)
   */
  async streamScreenSingleEye(
    side: 'OS' | 'OD',
    imageSrc: string,
    onEvent: (event: StreamEvent) => void
  ): Promise<BackendScreenResponse> {
    const blob = dataUrlToBlob(imageSrc);
    const formData = new FormData();
    formData.append('file', blob, `${side}_fundus.jpg`);

    const response = await fetch(`${BASE_URL}/api/screen-stream`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`Screen stream failed (HTTP ${response.status}): ${errText}`);
    }

    if (!response.body) {
      throw new Error('Response body is empty');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let finalResult: BackendScreenResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop() || '';

      for (const chunk of chunks) {
        const line = chunk.trim();
        if (line.startsWith('data: ')) {
          try {
            const parsed = JSON.parse(line.substring(6));
            if (parsed.type === 'stage') {
              onEvent({
                stage: parsed.name,
                name: parsed.name,
                message: parsed.message,
                data: parsed.data,
              });
            } else if (parsed.type === 'result') {
              finalResult = parsed.data as BackendScreenResponse;
            } else if (parsed.type === 'error') {
              throw new Error(parsed.message || 'Stream processing error');
            }
          } catch (e) {
            console.warn('Could not parse SSE chunk', line, e);
          }
        }
      }
    }

    if (!finalResult) {
      throw new Error('Screening stream finished without returning final result');
    }

    if (finalResult.status !== 'completed') {
      throw new Error(finalResult.message || 'Screening could not produce a valid analysis result');
    }

    return finalResult;
  }

  /**
   * Run image quality assessment for Left Eye and Right Eye
   */
  async assessQuality(
    eye: EyeData,
    onProgress?: (progress: number, stageName: string) => void
  ): Promise<ImageQualityMetrics> {
    if (!eye.imageSrc) {
      throw new Error(`No image uploaded for ${eye.sideLabel}`);
    }

    onProgress?.(25, 'Validating image format & headers...');
    onProgress?.(50, 'Analyzing focus (Laplacian variance)...');
    onProgress?.(75, 'Analyzing illumination & field of view...');

    try {
      const backendRes = await this.screenSingleEye(eye.side, eye.imageSrc);
      onProgress?.(100, 'Quality assessment complete');
      return this.mapQualityMetrics(backendRes.quality);
    } catch (err) {
      console.error('Quality assessment call failed:', err);
      // If backend is offline, inform user honestly
      return {
        focus: { status: 'Insufficient', details: 'Backend offline or unreachable' },
        illumination: { status: 'Insufficient', details: 'Backend offline or unreachable' },
        fieldOfView: { status: 'Insufficient', details: 'Backend offline or unreachable' },
        fundusValidity: { isValid: false, details: 'Could not connect to screening backend' },
        overallStatus: 'REJECTED',
        failureReasons: [`Backend unreachable: ${String(err)}`],
      };
    }
  }

  /**
   * Run Retinal Analysis Pipeline on both eyes and combine results
   */
  async streamRetinalAnalysis(
    exam: Examination,
    onEvent: (event: StreamEvent) => void
  ): Promise<Examination> {
    const updatedExam: Examination = JSON.parse(JSON.stringify(exam));

    // Process Left Eye if present
    if (exam.leftEye.imageSrc) {
      onEvent({
        stage: 'image_received',
        name: 'left_eye_start',
        message: 'Processing Left Eye (OS) image through screening pipeline...',
      });

      const osResult = await this.streamScreenSingleEye('OS', exam.leftEye.imageSrc, onEvent);
      this.populateEyeFromBackend(updatedExam.leftEye, osResult);
    }

    // Process Right Eye if present
    if (exam.rightEye.imageSrc) {
      onEvent({
        stage: 'image_received',
        name: 'right_eye_start',
        message: 'Processing Right Eye (OD) image through screening pipeline...',
      });

      const odResult = await this.streamScreenSingleEye('OD', exam.rightEye.imageSrc, onEvent);
      this.populateEyeFromBackend(updatedExam.rightEye, odResult);
    }

    // Calculate Combined / Overall Grade from bilateral results
    const grades: number[] = [];
    if (updatedExam.leftEye.predictionGrade !== null) grades.push(updatedExam.leftEye.predictionGrade);
    if (updatedExam.rightEye.predictionGrade !== null) grades.push(updatedExam.rightEye.predictionGrade);

    if (grades.length > 0) {
      // Overall grade is the maximum of bilateral eye grades (clinical worst-eye standard)
      const maxGrade = Math.max(...grades) as DRGradeIndex;
      updatedExam.overallGrade = maxGrade;

      const confidences: number[] = [];
      if (updatedExam.leftEye.confidence !== null) confidences.push(updatedExam.leftEye.confidence);
      if (updatedExam.rightEye.confidence !== null) confidences.push(updatedExam.rightEye.confidence);
      updatedExam.overallConfidence = confidences.length > 0 ? confidences.reduce((a, b) => a + b, 0) / confidences.length : null;

      const isReferable = maxGrade >= 2;
      updatedExam.overallReferable = isReferable;

      const refProbs: number[] = [];
      if (updatedExam.leftEye.probabilities) {
        refProbs.push(
          (updatedExam.leftEye.probabilities.grade2 || 0) +
          (updatedExam.leftEye.probabilities.grade3 || 0) +
          (updatedExam.leftEye.probabilities.grade4 || 0)
        );
      }
      if (updatedExam.rightEye.probabilities) {
        refProbs.push(
          (updatedExam.rightEye.probabilities.grade2 || 0) +
          (updatedExam.rightEye.probabilities.grade3 || 0) +
          (updatedExam.rightEye.probabilities.grade4 || 0)
        );
      }
      updatedExam.referableProbability = refProbs.length > 0 ? Math.max(...refProbs) : null;

      updatedExam.aiRecommendation = isReferable
        ? 'Referral recommended for comprehensive ophthalmological evaluation.'
        : 'Negative for referable diabetic retinopathy. Routine follow-up screening recommended.';

      const insights: string[] = [];
      if (isReferable) {
        insights.push(`Referable DR threshold met (Grade ${maxGrade}).`);
        insights.push('Recommend dilated fundus examination by a specialist.');
      } else {
        insights.push('No referable signs of diabetic retinopathy detected.');
        insights.push('Routine annual screening and glycemic management recommended.');
      }
      updatedExam.keyInsights = insights;
    }

    updatedExam.status = 'completed';
    return updatedExam;
  }

  private populateEyeFromBackend(eye: EyeData, res: BackendScreenResponse) {
    if (res.dr_prediction) {
      eye.predictionGrade = res.dr_prediction.grade as DRGradeIndex;
      eye.confidence = res.dr_prediction.confidence;

      const probs = res.dr_prediction.probabilities || {};
      const probDist: DRProbabilityDistribution = {
        grade0: probs['0'] ?? 0,
        grade1: probs['1'] ?? 0,
        grade2: probs['2'] ?? 0,
        grade3: probs['3'] ?? 0,
        grade4: probs['4'] ?? 0,
      };
      eye.probabilities = probDist;
    }

    if (res.referable_dr) {
      eye.isReferable = res.referable_dr.is_referable;
    }

    if (res.quality) {
      eye.quality = this.mapQualityMetrics(res.quality);
    }

    if (res.gradcam_image) {
      eye.gradCamSrc = res.gradcam_image;
      eye.gradCamAvailable = true;
    } else {
      eye.gradCamSrc = null;
      eye.gradCamAvailable = false;
    }

    if (res.enhanced_image) {
      eye.enhancedSrc = res.enhanced_image;
      eye.enhancedAvailable = true;
    } else {
      eye.enhancedSrc = null;
      eye.enhancedAvailable = false;
    }

    if (res.lesions) {
      const evidence: RetinalEvidence = {
        microaneurysms: res.lesions.microaneurysms ? { count: res.lesions.microaneurysms.count, confidence: res.lesions.microaneurysms.confidence ?? 0 } : null,
        hemorrhages: res.lesions.hemorrhages ? { count: res.lesions.hemorrhages.count, confidence: res.lesions.hemorrhages.confidence ?? 0 } : null,
        exudates: res.lesions.exudates ? { count: res.lesions.exudates.count, confidence: res.lesions.exudates.confidence ?? 0 } : null,
        vesselAbnormalities: res.lesions.vessels?.quality === 'High density' ? 'Moderate' : res.lesions.vessels?.quality === 'Normal' ? 'Mild' : 'Not available',
        macularInvolvement: false,
        statusNote: 'Computer-vision heuristic evidence; ophthalmologist confirmation required',
      };
      eye.evidence = evidence;
    }
  }

  /**
   * Save Clinician Review (Local persistent storage with audit ID)
   */
  async saveClinicalReview(examId: string, review: Examination['clinicalReview']): Promise<{ success: boolean; auditId: string }> {
    const auditId = `AUDIT-${examId.replace('#', '')}-${Date.now().toString().slice(-6)}`;
    try {
      localStorage.setItem(`review_${examId}`, JSON.stringify({ ...review, auditId, savedAt: new Date().toISOString() }));
    } catch {
      // LocalStorage fallback
    }
    return { success: true, auditId };
  }

  /**
   * Export Examination Data (CSV format)
   */
  exportExamCsv(exam: Examination): string {
    const headers = [
      'Patient ID', 'Patient Name', 'Age', 'Sex', 'Division', 'Exam Date',
      'Model Version', 'AI Overall Grade', 'AI Referable', 'Referable Prob',
      'OS Grade', 'OS Conf', 'OD Grade', 'OD Conf',
      'Clinician Reviewer', 'Clinician Grade', 'Clinician Referable', 'Clinician Notes',
    ];

    const row = [
      `"${exam.patient.id || 'N/A'}"`,
      `"${exam.patient.name || 'Unregistered'}"`,
      exam.patient.age || 'N/A',
      `"${exam.patient.sex || 'N/A'}"`,
      `"${exam.patient.villageOrDistrict || 'N/A'}"`,
      `"${exam.timestamp}"`,
      `"${exam.modelVersion}"`,
      exam.overallGrade !== null ? `Grade ${exam.overallGrade}` : 'N/A',
      exam.overallReferable !== null ? (exam.overallReferable ? 'YES' : 'NO') : 'N/A',
      exam.referableProbability !== null ? `${(exam.referableProbability * 100).toFixed(1)}%` : 'N/A',
      exam.leftEye.predictionGrade !== null ? `Grade ${exam.leftEye.predictionGrade}` : 'N/A',
      exam.leftEye.confidence !== null ? `${(exam.leftEye.confidence * 100).toFixed(1)}%` : 'N/A',
      exam.rightEye.predictionGrade !== null ? `Grade ${exam.rightEye.predictionGrade}` : 'N/A',
      exam.rightEye.confidence !== null ? `${(exam.rightEye.confidence * 100).toFixed(1)}%` : 'N/A',
      `"${exam.clinicalReview.reviewerName || 'Unassigned'}"`,
      exam.clinicalReview.clinicalGrade !== null ? `Grade ${exam.clinicalReview.clinicalGrade}` : 'Pending',
      exam.clinicalReview.clinicalReferable !== null ? (exam.clinicalReview.clinicalReferable ? 'YES' : 'NO') : 'Pending',
      `"${(exam.clinicalReview.clinicalNotes || '').replace(/"/g, '""')}"`,
    ];

    return `${headers.join(',')}\n${row.join(',')}`;
  }
}

export const apiService = ClinicalApiService.getInstance();

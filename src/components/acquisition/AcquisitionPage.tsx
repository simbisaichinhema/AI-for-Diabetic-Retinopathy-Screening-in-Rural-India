/**
 * INFINITE LOOPS — SIH26038
 * Image Acquisition Workstation
 * Supports live camera capture & fundus photograph upload with anatomical positioning.
 */

import React, { useRef, useState, useCallback, useEffect } from 'react';
import {
  Upload,
  RotateCcw,
  ArrowRight,
  CheckCircle2,
  Camera,
  CameraOff,
  Aperture,
  AlertCircle,
  X,
  ZoomIn,
} from 'lucide-react';
import { useScreening } from '../../context/ScreeningContext';

type CameraState =
  | { status: 'idle' }
  | { status: 'requesting' }
  | { status: 'no_device'; message: string }
  | { status: 'permission_denied' }
  | { status: 'live'; stream: MediaStream; deviceLabel: string }
  | { status: 'error'; message: string };

export const AcquisitionPage: React.FC = () => {
  const {
    activeEye,
    setActiveEye,
    exam,
    uploadEyeImage,
    retakeEye,
    runQualityAssessment,
  } = useScreening();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraState, setCameraState] = useState<CameraState>({ status: 'idle' });

  const isLeftEye = activeEye === 'OS';
  const currentEyeData = isLeftEye ? exam.leftEye : exam.rightEye;
  const isCurrentCaptured = !!currentEyeData.imageSrc;
  const isLeftCaptured = !!exam.leftEye.imageSrc;
  const isRightCaptured = !!exam.rightEye.imageSrc;
  const bothCaptured = isLeftCaptured && isRightCaptured;

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCameraState({ status: 'idle' });
  }, []);

  useEffect(() => {
    stopCamera();
  }, [activeEye, stopCamera]);

  useEffect(() => {
    return () => stopCamera();
  }, [stopCamera]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadEyeImage(activeEye, file);
    e.target.value = '';
  };

  const handleNext = () => {
    stopCamera();
    if (isLeftEye) {
      setActiveEye('OD');
    } else if (bothCaptured) {
      runQualityAssessment();
    }
  };

  const handleOpenCamera = async (mode: 'fundus' | 'webcam-demo') => {
    setCameraState({ status: 'requesting' });

    try {
      let devices: MediaDeviceInfo[] = [];
      try {
        const probe = await navigator.mediaDevices.getUserMedia({ video: true });
        probe.getTracks().forEach((t) => t.stop());
        devices = await navigator.mediaDevices.enumerateDevices();
      } catch (permErr: unknown) {
        if (permErr instanceof DOMException && permErr.name === 'NotAllowedError') {
          setCameraState({ status: 'permission_denied' });
          return;
        }
        setCameraState({
          status: 'no_device',
          message: 'Please plug in the fundus camera to start scanning.',
        });
        return;
      }

      const videoDevices = devices.filter((d) => d.kind === 'videoinput');

      if (videoDevices.length === 0) {
        setCameraState({
          status: 'no_device',
          message: 'No camera detected. Please plug in the fundus camera to start scanning.',
        });
        return;
      }

      const fundusKeywords = ['fundus', 'retinal', 'ophthalmic', 'topcon', 'zeiss', 'canon', 'kowa', 'nidek'];
      const fundusDevice = videoDevices.find((d) =>
        fundusKeywords.some((kw) => d.label.toLowerCase().includes(kw))
      );

      if (mode === 'fundus' && !fundusDevice) {
        setCameraState({
          status: 'no_device',
          message: 'No recognized fundus camera found. Use the separate webcam demo option only for presentation testing.',
        });
        return;
      }

      const preferredDevice = fundusDevice ?? videoDevices[0];

      const constraints: MediaStreamConstraints = {
        video: {
          deviceId: { exact: preferredDevice.deviceId },
          width: { ideal: 3840 },
          height: { ideal: 2160 },
        },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;

      setCameraState({
        status: 'live',
        stream,
        deviceLabel: mode === 'webcam-demo'
          ? 'WEBCAM DEMO · NOT CLINICALLY ACCURATE'
          : preferredDevice.label || `Fundus Camera ${videoDevices.indexOf(preferredDevice) + 1}`,
      });

      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown camera error';
      setCameraState({ status: 'error', message: msg });
    }
  };

  const handleCaptureFrame = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    canvas.width = video.videoWidth || 1920;
    canvas.height = video.videoHeight || 1080;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/png');

    const eyeLabel = isLeftEye ? 'OS' : 'OD';
    uploadEyeImage(activeEye, {
      name: `fundus_capture_${eyeLabel}_${Date.now()}.png`,
      dataUrl,
    });

    stopCamera();
  };

  const isLive = cameraState.status === 'live';

  return (
    <div className="acq-workstation">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/png,image/jpeg,image/jpg,image/webp,image/tiff"
        style={{ display: 'none' }}
      />
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      <div className={`acq-card-container ${isLeftEye ? 'eye-mode-os' : 'eye-mode-od'}`}>

        {/* ANATOMICAL HEAD OR CAMERA VIEWFINDER */}
        <div className="acq-visual-column">
          {isLive ? (
            <div className="acq-viewfinder-wrap">
              <video
                ref={videoRef}
                className="acq-viewfinder-video"
                autoPlay
                muted
                playsInline
              />
              <div className="acq-reticle" aria-hidden="true">
                <div className="acq-crosshair" />
              </div>
              <div className="acq-device-pill">
                <ZoomIn size={12} />
                <span>{cameraState.status === 'live' ? cameraState.deviceLabel : 'Camera'}</span>
              </div>
              <button
                type="button"
                className="acq-close-cam-btn"
                onClick={stopCamera}
                title="Close camera"
              >
                <X size={15} />
              </button>
            </div>
          ) : (
            <div className="acq-head-wrap">
              <img
                src={isLeftEye ? '/assets/head_exact_left.jpg' : '/assets/head_exact_right.jpg'}
                alt={isLeftEye ? 'Left eye (OS)' : 'Right eye (OD)'}
                className="acq-head-img"
              />
              <div className={`acq-eye-badge ${isLeftEye ? 'badge-left' : 'badge-right'}`}>
                {isLeftEye ? 'LEFT EYE (OS) TARGET' : 'RIGHT EYE (OD) TARGET'}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: CONTROLS & ACTIONS */}
        <div className="acq-controls-column">
          
          {/* Header */}
          <div className="acq-header-block">
            <div className="acq-step-badge">
              {isLeftEye ? 'STEP 1 OF 2 · LEFT EYE (OS)' : 'STEP 2 OF 2 · RIGHT EYE (OD)'}
            </div>
            <h2 className="acq-main-heading">
              {isLeftEye ? 'Acquire Left Eye (OS) Retinal Fundus' : 'Acquire Right Eye (OD) Retinal Fundus'}
            </h2>
          </div>

          {/* Camera Notices */}
          {cameraState.status === 'no_device' && (
            <div className="acq-alert acq-alert--warn">
              <CameraOff size={16} />
              <div>
                <strong>Fundus Camera Not Detected</strong>
                <p>{cameraState.message}</p>
              </div>
            </div>
          )}
          {cameraState.status === 'permission_denied' && (
            <div className="acq-alert acq-alert--warn">
              <AlertCircle size={16} />
              <div>
                <strong>Camera Permission Denied</strong>
                <p>Please allow camera permissions in your browser to scan directly.</p>
              </div>
            </div>
          )}
          {cameraState.status === 'error' && (
            <div className="acq-alert acq-alert--error">
              <AlertCircle size={16} />
              <div>
                <strong>Camera Error</strong>
                <p>{cameraState.message}</p>
              </div>
            </div>
          )}

          {/* Action Zone */}
          {isCurrentCaptured ? (
            <div className="acq-captured-card">
              <img
                src={currentEyeData.imageSrc!}
                alt="Captured Retinal Image"
                className="acq-captured-thumb"
              />
              <div className="acq-captured-details">
                <div className="acq-captured-title">
                  <CheckCircle2 size={16} className="text-green" />
                  <span>{isLeftEye ? 'Left Eye (OS)' : 'Right Eye (OD)'} Acquired</span>
                </div>
                <div className="acq-captured-meta">
                  {currentEyeData.fileName || 'fundus_capture.png'}
                </div>
              </div>
              <div className="acq-captured-btns">
                <button
                  type="button"
                  className="btn-acq-replace"
                  onClick={() => retakeEye(activeEye)}
                >
                  <RotateCcw size={14} /> Retake
                </button>
                <button
                  type="button"
                  className="btn-acq-next"
                  onClick={handleNext}
                >
                  <span>{isLeftEye ? 'Next: Right Eye (OD)' : 'Run Quality Gate'}</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          ) : (
            <div className="acq-action-buttons">
              {isLive ? (
                <button
                  type="button"
                  className="btn-acq-capture"
                  onClick={handleCaptureFrame}
                >
                  <Aperture size={20} />
                  <span>Capture Still Frame</span>
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="btn-acq-main-cam"
                    onClick={() => handleOpenCamera('fundus')}
                    disabled={cameraState.status === 'requesting'}
                  >
                    <Camera size={20} />
                    <div className="btn-main-text-group">
                      <span className="btn-main-title">
                        {cameraState.status === 'requesting' ? 'Connecting to Camera...' : 'Capture from Fundus Camera'}
                      </span>
                      <span className="btn-main-sub">
                        Connects directly to attached USB or ophthalmic optical imager
                      </span>
                    </div>
                  </button>

                  <button
                    type="button"
                    className="btn-acq-webcam-demo"
                    onClick={() => handleOpenCamera('webcam-demo')}
                    disabled={cameraState.status === 'requesting'}
                  >
                    <Camera size={15} />
                    <span>Use Webcam for Demo Only</span>
                  </button>

                  <p className="acq-demo-warning">
                    Demo webcam capture is for presentation flow testing only and is not a clinically accurate fundus image source.
                  </p>

                  <div className="acq-or-divider">
                    <span>or upload fundus file</span>
                  </div>

                  <button
                    type="button"
                    className="btn-acq-upload-file"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload size={16} />
                    <span>Upload Retinal Image (PNG / JPEG / WebP)</span>
                  </button>
                </>
              )}
            </div>
          )}

          {/* Bilateral Progress Tracker */}
          <div className="acq-bilateral-bar">
            <div
              className={`acq-eye-chip ${isLeftCaptured ? 'chip-done' : isLeftEye ? 'chip-active' : ''}`}
              onClick={() => { stopCamera(); setActiveEye('OS'); }}
            >
              <span className="chip-eye-name">Left Eye (OS)</span>
              <span className="chip-eye-status">
                {isLeftCaptured ? '✓ Acquired' : isLeftEye ? 'In Progress' : 'Pending'}
              </span>
            </div>

            <div
              className={`acq-eye-chip ${isRightCaptured ? 'chip-done' : !isLeftEye ? 'chip-active' : ''}`}
              onClick={() => { stopCamera(); setActiveEye('OD'); }}
            >
              <span className="chip-eye-name">Right Eye (OD)</span>
              <span className="chip-eye-status">
                {isRightCaptured ? '✓ Acquired' : !isLeftEye ? 'In Progress' : 'Pending'}
              </span>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

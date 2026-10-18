"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import {
  Camera,
  RefreshCw,
  X,
  AlertCircle,
  Upload,
  Check,
  Loader2,
  Sparkles,
  Smartphone,
  ShieldAlert,
} from "lucide-react";
import { ACCEPTED_IMAGE_TYPES } from "../constants/upload";
import { useTranslation } from "../i18n/I18nContext";

interface CameraCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

type CameraStatus =
  | "idle"
  | "requesting_permission"
  | "initializing"
  | "ready"
  | "error"
  | "capturing"
  | "captured";

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({
  isOpen,
  onClose,
  onCapture,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const nativeFileInputRef = useRef<HTMLInputElement | null>(null);
  const nativeCameraInputRef = useRef<HTMLInputElement | null>(null);
  const initTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isStartingRef = useRef<boolean>(false);

  const [cameraStatus, setCameraStatus] = useState<CameraStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const { t } = useTranslation();

  // Helper to cleanly stop all tracks in active media stream
  const stopActiveStream = useCallback(() => {
    if (initTimerRef.current) {
      clearInterval(initTimerRef.current);
      initTimerRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // Ignore track stop errors during teardown
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    isStartingRef.current = false;
  }, []);

  // Keyboard accessibility: close on Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Robust camera stream initialization
  const startCamera = useCallback(async () => {
    if (isStartingRef.current) return;
    isStartingRef.current = true;
    stopActiveStream();

    // Check secure context requirement (browsers block getUserMedia on insecure origins)
    if (typeof window !== "undefined" && window.isSecureContext === false) {
      setError(
        "Camera access requires a secure connection (HTTPS or localhost). Current browser origin is insecure. You can upload a photo or use your device camera below."
      );
      setCameraStatus("error");
      isStartingRef.current = false;
      return;
    }

    if (typeof window === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setError(
        "Camera API is not supported in this browser environment. You can upload a photo or use your device camera below."
      );
      setCameraStatus("error");
      isStartingRef.current = false;
      return;
    }

    setCameraStatus("requesting_permission");
    setError(null);
    setCapturedBlob(null);

    let mediaStream: MediaStream | null = null;

    try {
      // 1. Try preferred rear camera (ideal for menus) with relaxed resolution limits
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });
    } catch {
      // 2. Fallback to any available video camera
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        });
      } catch (fallbackErr: unknown) {
        isStartingRef.current = false;
        const errObj = fallbackErr as Error;
        let friendlyMessage = "Unable to access camera device.";

        if (
          errObj.name === "NotAllowedError" ||
          errObj.name === "PermissionDeniedError"
        ) {
          friendlyMessage =
            "Camera permission was denied. Please allow camera access in your browser address bar or select an image file below.";
        } else if (
          errObj.name === "NotFoundError" ||
          errObj.name === "DevicesNotFoundError"
        ) {
          friendlyMessage =
            "No camera was found on this device. You can upload an image file instead.";
        } else if (
          errObj.name === "NotReadableError" ||
          errObj.name === "TrackStartError"
        ) {
          friendlyMessage =
            "Camera is currently in use by another application. Please close other camera apps and retry.";
        } else if (errObj.message) {
          friendlyMessage = errObj.message;
        }

        setError(friendlyMessage);
        setCameraStatus("error");
        return;
      }
    }

    streamRef.current = mediaStream;
    setCameraStatus("initializing");

    const video = videoRef.current;
    if (video) {
      video.srcObject = mediaStream;
      video.muted = true;
      video.playsInline = true;
      video.autoplay = true;

      const markReady = () => {
        setCameraStatus("ready");
        isStartingRef.current = false;
      };

      video.onloadedmetadata = () => {
        if (video.videoWidth > 0) markReady();
      };
      video.oncanplay = markReady;
      video.onplaying = markReady;

      try {
        await video.play();
        if (video.videoWidth > 0) {
          markReady();
        }
      } catch {
        // Handled by oncanplay/onplaying
      }

      // Safety polling interval: ensure ready is marked within 1.5s if stream is active
      let attempts = 0;
      initTimerRef.current = setInterval(() => {
        attempts++;
        if (
          video.videoWidth > 0 ||
          video.readyState >= 2 ||
          (mediaStream && mediaStream.active && attempts >= 8)
        ) {
          markReady();
          if (initTimerRef.current) {
            clearInterval(initTimerRef.current);
            initTimerRef.current = null;
          }
        }
      }, 150);
    } else {
      isStartingRef.current = false;
    }
  }, [stopActiveStream]);

  // Main lifecycle: Initialize stream once when modal opens, teardown when it closes
  useEffect(() => {
    if (!isOpen) {
      stopActiveStream();
      setCameraStatus("idle");
      setError(null);
      setCapturedBlob(null);
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
        setPreviewUrl(null);
      }
      return;
    }

    startCamera();

    return () => {
      stopActiveStream();
    };
  }, [isOpen, startCamera, stopActiveStream]);

  // Capture current high-res frame from video stream to canvas
  const handleCaptureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    setCameraStatus("capturing");

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setCameraStatus("ready");
      return;
    }

    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCapturedBlob(blob);
          const url = URL.createObjectURL(blob);
          setPreviewUrl(url);
          setCameraStatus("captured");
          // Stop live stream to conserve battery & release camera device
          stopActiveStream();
        } else {
          setCameraStatus("ready");
        }
      },
      "image/jpeg",
      0.95
    );
  };

  // Confirm and send captured frame to parent analysis handler
  const handleConfirmCapture = () => {
    if (!capturedBlob) return;
    const file = new File([capturedBlob], `menu_scan_${Date.now()}.jpg`, {
      type: "image/jpeg",
    });
    onCapture(file);
    onClose();
  };

  // Retake photo: restart live viewfinder
  const handleRetake = () => {
    setCapturedBlob(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    startCamera();
  };

  // Direct file input fallback
  const handleNativeFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onCapture(file);
      onClose();
    }
    e.target.value = "";
  };

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      onClick={handleBackdropClick}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#1F1B18]/75 backdrop-blur-md p-4 animate-in fade-in duration-200"
      role="dialog"
      aria-modal="true"
      aria-label="Menu Camera Viewfinder"
    >
      {/* Hidden File Inputs for Fallbacks */}
      <input
        ref={nativeFileInputRef}
        type="file"
        accept={ACCEPTED_IMAGE_TYPES}
        className="sr-only"
        onChange={handleNativeFileInput}
      />
      <input
        ref={nativeCameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        onChange={handleNativeFileInput}
      />

      <div className="relative w-full max-w-2xl bg-[#FFF8F5] border border-[#EADFD5] rounded-3xl overflow-hidden shadow-2xl flex flex-col h-[580px] max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#EADFD5] bg-[#FFF8F5] shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#FBF2ED] text-[#C74735] border border-[#F2DFD3]">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#1F1B18] tracking-tight">
                {t("camera.viewfinderTitle")}
              </h3>
              <p className="text-xs text-[#70645C]">
                {t("camera.viewfinderSub")}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl text-[#70645C] hover:text-[#1F1B18] hover:bg-[#F2DFD3] transition-colors cursor-pointer"
            aria-label="Close camera modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stable Viewfinder Container with fixed layout bounds */}
        <div className="relative flex-1 bg-[#1F1B18] overflow-hidden flex items-center justify-center min-h-0">
          {error ? (
            /* Error Fallback Screen */
            <div className="flex flex-col items-center justify-center p-6 text-center max-w-md gap-4">
              <div className="w-14 h-14 rounded-2xl bg-[#FFDAD6] border border-[#FFDAD6] text-[#BA1A1A] flex items-center justify-center shadow-md">
                <ShieldAlert className="w-7 h-7" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-[#FFF8F5]">
                  {t("camera.unavailableTitle")}
                </h4>
                <p className="text-xs text-[#EADFD5]/90 mt-1.5 leading-relaxed">
                  {error}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-2.5 w-full pt-2">
                <button
                  type="button"
                  onClick={startCamera}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#C74735] hover:bg-[#A93629] text-white text-xs font-semibold cursor-pointer shadow-lg shadow-[#C74735]/25 transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <RefreshCw className="w-4 h-4" />
                  {t("camera.retry")}
                </button>
                <button
                  type="button"
                  onClick={() => nativeCameraInputRef.current?.click()}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#FFFFFF] hover:bg-[#FBF2ED] text-[#1F1B18] text-xs font-semibold border border-[#EADFD5] cursor-pointer transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Smartphone className="w-4 h-4 text-[#C74735]" />
                  {t("camera.deviceCamera")}
                </button>
                <button
                  type="button"
                  onClick={() => nativeFileInputRef.current?.click()}
                  className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-[#FFFFFF] hover:bg-[#FBF2ED] text-[#1F1B18] text-xs font-semibold border border-[#EADFD5] cursor-pointer transition-all hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Upload className="w-4 h-4 text-[#C74735]" />
                  {t("camera.uploadPhoto")}
                </button>
              </div>
            </div>
          ) : previewUrl ? (
            /* Captured Frame Preview */
            <div className="relative w-full h-full flex items-center justify-center bg-[#1F1B18]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Captured Menu Preview"
                className="w-full h-full object-contain"
              />
              <div className="absolute top-4 left-4 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EAF5EE] text-[11px] font-semibold text-[#166742] border border-[#B2DEC4] shadow-md">
                <Sparkles className="w-3.5 h-3.5" />
                {t("camera.capturedReady")}
              </div>
            </div>
          ) : (
            /* Live Camera Stream with Stable Layout */
            <div className="relative w-full h-full flex items-center justify-center bg-[#1F1B18]">
              <video
                ref={videoRef}
                playsInline
                muted
                autoPlay
                className="absolute inset-0 w-full h-full object-cover"
              />

              {/* Status Overlay while initializing or requesting permission */}
              {cameraStatus !== "ready" && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#1F1B18]/85 backdrop-blur-sm gap-3 z-10 p-6 text-center">
                  <Loader2 className="w-8 h-8 text-[#C74735] animate-spin" />
                  <p className="text-sm font-semibold text-[#FFF8F5]">
                    {cameraStatus === "requesting_permission"
                      ? t("camera.waitingPermission")
                      : t("camera.initSensor")}
                  </p>
                  <p className="text-xs text-[#EADFD5]/80 max-w-xs">
                    {t("camera.promptNotice")}
                  </p>
                  <button
                    type="button"
                    onClick={startCamera}
                    className="mt-2 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#C74735] hover:bg-[#A93629] text-white text-xs font-semibold shadow-md cursor-pointer transition-all active:scale-95"
                  >
                    <Camera className="w-4 h-4" />
                    <span>{t("camera.grantButton")}</span>
                  </button>
                </div>
              )}

              {/* Viewfinder Framing Guide - Active only when camera is ready */}
              {cameraStatus === "ready" && (
                <>
                  <div className="absolute top-4 left-4 inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FFF8F5]/90 backdrop-blur-md text-[11px] font-semibold text-[#166742] border border-[#B2DEC4] shadow-sm">
                    <div className="w-2 h-2 rounded-full bg-[#166742] animate-ping" />
                    {t("camera.liveBadge")}
                  </div>

                  <div className="absolute inset-8 sm:inset-12 border border-[#C74735]/40 rounded-2xl pointer-events-none flex flex-col justify-between p-4 shadow-[0_0_20px_rgba(199,71,53,0.15)]">
                    <div className="flex justify-between">
                      <div className="w-7 h-7 border-t-3 border-l-3 border-[#C74735] rounded-tl-lg" />
                      <div className="w-7 h-7 border-t-3 border-r-3 border-[#C74735] rounded-tr-lg" />
                    </div>
                    <div className="text-center text-[11px] text-[#FFF8F5] font-medium bg-[#1F1B18]/80 px-4 py-1.5 rounded-full mx-auto backdrop-blur-sm border border-[#EADFD5]/20 shadow-md">
                      {t("camera.holdSteady")}
                    </div>
                    <div className="flex justify-between">
                      <div className="w-7 h-7 border-b-3 border-l-3 border-[#C74735] rounded-bl-lg" />
                      <div className="w-7 h-7 border-b-3 border-r-3 border-[#C74735] rounded-br-lg" />
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Hidden Canvas for high-res snapshot */}
          <canvas ref={canvasRef} className="sr-only" />
        </div>

        {/* Footer Action Bar */}
        <div className="px-6 py-4 bg-[#FFF8F5] border-t border-[#EADFD5] flex items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => nativeFileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#70645C] hover:text-[#C74735] cursor-pointer transition-colors p-1"
            >
              <Upload className="w-4 h-4" />
              <span>{t("camera.uploadPhoto")}</span>
            </button>
            <span className="text-[#EADFD5]">|</span>
            <button
              type="button"
              onClick={() => nativeCameraInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#70645C] hover:text-[#C74735] cursor-pointer transition-colors p-1"
            >
              <Smartphone className="w-4 h-4" />
              <span>{t("camera.deviceCamera")}</span>
            </button>
          </div>

          {previewUrl ? (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleRetake}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#FBF2ED] hover:bg-[#F2DFD3] text-[#1F1B18] text-xs font-semibold border border-[#EADFD5] transition-colors cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                {t("camera.retake")}
              </button>
              <button
                type="button"
                onClick={handleConfirmCapture}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#C74735] hover:bg-[#A93629] text-white text-xs font-semibold shadow-lg shadow-[#C74735]/25 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" />
                {t("camera.analyzeMenu")}
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleCaptureFrame}
              disabled={cameraStatus !== "ready"}
              className="inline-flex items-center gap-2.5 px-6 py-2.5 rounded-full bg-[#C74735] hover:bg-[#A93629] disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-bold shadow-lg shadow-[#C74735]/25 transition-all active:scale-95 cursor-pointer"
            >
              {cameraStatus === "ready" ? (
                <>
                  <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                  {t("camera.capturePhoto")}
                </>
              ) : (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  {cameraStatus === "requesting_permission"
                    ? t("camera.waitingPermission")
                    : t("camera.initSensor")}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

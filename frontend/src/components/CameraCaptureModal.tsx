"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { Camera, RefreshCw, X, AlertCircle, Upload, Check } from "lucide-react";

interface CameraCaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCapture: (file: File) => void;
}

export const CameraCaptureModal: React.FC<CameraCaptureModalProps> = ({
  isOpen,
  onClose,
  onCapture,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isStartingCamera, setIsStartingCamera] = useState(false);

  const stopStream = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  const startCamera = useCallback(async () => {
    setError(null);
    setIsStartingCamera(true);
    setCapturedBlob(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Camera API is not supported in this browser environment.");
      }

      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        await videoRef.current.play().catch(() => {});
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unable to access camera device.";
      setError(msg);
    } finally {
      setIsStartingCamera(false);
    }
  }, [previewUrl]);

  useEffect(() => {
    let isCancelled = false;

    if (isOpen) {
      const initCamera = async () => {
        try {
          if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Camera API is not supported in this browser environment.");
          }

          const mediaStream = await navigator.mediaDevices.getUserMedia({
            video: {
              facingMode: { ideal: "environment" },
              width: { ideal: 1920 },
              height: { ideal: 1080 },
            },
            audio: false,
          });

          if (!isCancelled) {
            setStream(mediaStream);
            if (videoRef.current) {
              videoRef.current.srcObject = mediaStream;
              await videoRef.current.play().catch(() => {});
            }
          } else {
            mediaStream.getTracks().forEach((t) => t.stop());
          }
        } catch (err: unknown) {
          if (!isCancelled) {
            const msg = err instanceof Error ? err.message : "Unable to access camera device.";
            setError(msg);
          }
        }
      };

      initCamera();
    }

    return () => {
      isCancelled = true;
      stopStream();
    };
  }, [isOpen, stopStream]);

  const handleCaptureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob((blob) => {
      if (blob) {
        setCapturedBlob(blob);
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
        stopStream();
      }
    }, "image/jpeg", 0.95);
  };

  const handleConfirmCapture = () => {
    if (!capturedBlob) return;
    const file = new File([capturedBlob], `menu_capture_${Date.now()}.jpg`, {
      type: "image/jpeg",
    });
    onCapture(file);
    onClose();
  };

  const handleRetake = () => {
    setCapturedBlob(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    startCamera();
  };

  const handleNativeFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onCapture(file);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl flex flex-col max-h-[92vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800/80 bg-slate-900/90">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Menu Camera Capture</h3>
              <p className="text-[11px] text-slate-400">Position the printed menu inside the viewfinder</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            aria-label="Close camera"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Viewfinder / Preview Canvas */}
        <div className="relative flex-1 bg-black flex items-center justify-center overflow-hidden min-h-[320px] sm:min-h-[440px]">
          {error ? (
            <div className="flex flex-col items-center justify-center p-6 text-center max-w-sm gap-4">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-rose-300">Camera Access Error</h4>
                <p className="text-xs text-slate-400 mt-1">{error}</p>
              </div>
              <label className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium cursor-pointer shadow-lg shadow-indigo-600/20 transition-all">
                <Upload className="w-4 h-4" />
                Upload Photo Instead
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={handleNativeFileInput}
                />
              </label>
            </div>
          ) : previewUrl ? (
            /* Still Capture Preview */
            <div className="relative w-full h-full flex items-center justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={previewUrl}
                alt="Captured Menu Preview"
                className="max-h-[70vh] w-auto object-contain"
              />
              <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-slate-900/80 backdrop-blur-md text-[11px] font-medium text-emerald-400 border border-emerald-500/30">
                Capture Ready
              </div>
            </div>
          ) : (
            /* Live Camera Stream */
            <div className="relative w-full h-full flex items-center justify-center">
              <video
                ref={videoRef}
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              {/* Viewfinder Framing Guide */}
              <div className="absolute inset-8 sm:inset-12 border-2 border-dashed border-indigo-400/50 rounded-2xl pointer-events-none flex flex-col justify-between p-4">
                <div className="flex justify-between">
                  <div className="w-6 h-6 border-t-2 border-l-2 border-indigo-400" />
                  <div className="w-6 h-6 border-t-2 border-r-2 border-indigo-400" />
                </div>
                <div className="text-center text-[11px] text-slate-300 font-medium bg-slate-950/60 px-3 py-1 rounded-full mx-auto backdrop-blur-sm">
                  Align dishes within guide
                </div>
                <div className="flex justify-between">
                  <div className="w-6 h-6 border-b-2 border-l-2 border-indigo-400" />
                  <div className="w-6 h-6 border-b-2 border-r-2 border-indigo-400" />
                </div>
              </div>
            </div>
          )}

          {/* Hidden Canvas for raster snapshot */}
          <canvas ref={canvasRef} className="hidden" />
        </div>

        {/* Action Controls Bar */}
        <div className="px-6 py-4 bg-slate-900/90 border-t border-slate-800/80 flex items-center justify-between gap-4">
          <label className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 cursor-pointer">
            <Upload className="w-4 h-4" />
            <span>Select file</span>
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={handleNativeFileInput}
            />
          </label>

          {previewUrl ? (
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={handleRetake}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retake
              </button>
              <button
                type="button"
                onClick={handleConfirmCapture}
                className="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-lg shadow-indigo-600/20 transition-all"
              >
                <Check className="w-3.5 h-3.5" />
                Analyze Menu
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={handleCaptureFrame}
              disabled={!stream || isStartingCamera}
              className="inline-flex items-center gap-2.5 px-6 py-2.5 rounded-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-semibold shadow-xl shadow-indigo-600/30 transition-all active:scale-95"
            >
              <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
              Capture Photo
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

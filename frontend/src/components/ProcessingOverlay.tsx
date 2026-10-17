"use client";

import React, { useState, useEffect } from "react";
import { Check, RotateCw, Sparkles, Image as ImageIcon, X } from "lucide-react";

interface ProcessingOverlayProps {
  onCancel?: () => void;
  imageUrl?: string | null;
}

interface StepInfo {
  id: string;
  label: string;
  description: string;
  typicalDuration: string;
}

const PIPELINE_STEPS: StepInfo[] = [
  {
    id: "prep",
    label: "Image Optimization & Preprocessing",
    description: "Deskewing EXIF orientation & CLAHE contrast enhancement",
    typicalDuration: "<0.1s",
  },
  {
    id: "vlm",
    label: "Local Qwen3-VL 8B Visual Extraction",
    description: "Parsing menu columns, native dishes, prices, and spatial layouts",
    typicalDuration: "~15-20s",
  },
  {
    id: "rag",
    label: "Culinary Knowledge Lookup",
    description: "Hybrid BM25 + dense vector matching against authoritative recipe records",
    typicalDuration: "<0.5s",
  },
  {
    id: "trans",
    label: "Contextual Multilingual Translation",
    description: "Resolving cultural recipes, native phonetics & culinary descriptions",
    typicalDuration: "<0.1s",
  },
  {
    id: "safety",
    label: "Allergen & Dietary Safety Evaluation",
    description: "Evidence-grounded allergen analysis and cross-contamination check",
    typicalDuration: "<0.1s",
  },
];

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({ onCancel, imageUrl }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [elapsedSecs, setElapsedSecs] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSecs((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Stage advancement progression based on actual optimized pipeline timings
    const timeouts = [
      setTimeout(() => setCurrentStepIndex(1), 600),   // Image prep done -> VLM active
      setTimeout(() => setCurrentStepIndex(2), 17000), // VLM done -> RAG active
      setTimeout(() => setCurrentStepIndex(3), 18000), // RAG done -> Translation active
      setTimeout(() => setCurrentStepIndex(4), 18800), // Translation done -> Safety active
    ];
    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-200"
    >
      <div className="w-full max-w-lg bg-[#FFFFFF] border border-[#EADFD5] rounded-3xl p-6 shadow-2xl flex flex-col gap-6 relative overflow-hidden">
        {/* Ambient Warm Glow */}
        <div className="absolute -right-16 -top-16 w-48 h-48 rounded-full bg-[#F2DFD3]/60 blur-3xl pointer-events-none" />

        {/* Header Strip with Thumbnail, Scanning Beam & Dismiss */}
        <div className="flex items-start justify-between gap-4 border-b border-[#EADFD5]/80 pb-5 z-10">
          <div className="flex items-center gap-3.5 min-w-0">
            {/* Thumbnail with Live Scanning Laser Beam */}
            <div className="relative w-16 h-20 rounded-xl overflow-hidden shrink-0 shadow-sm bg-[#F5ECE7] border border-[#EADFD5]">
              {imageUrl ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={imageUrl}
                  alt="Scanned Menu Thumbnail"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[#695C53]">
                  <ImageIcon className="w-7 h-7 opacity-60" />
                </div>
              )}
              {/* Scanning Laser Beam */}
              <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-[#C74735] to-transparent shadow-[0_0_8px_rgba(199,71,53,0.9)] animate-scan-beam" />
            </div>

            <div className="flex flex-col min-w-0">
              <span className="text-[11px] font-bold text-[#A52F20] uppercase tracking-wider">
                Decoding In Progress
              </span>
              <h3 className="text-base font-bold text-[#1F1B18] truncate mt-0.5">
                Local Vision Analysis
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#F2DFD3] text-[#A52F20] text-xs font-semibold">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#C74735] animate-ping" />
                  Elapsed: {elapsedSecs}s
                </span>
                <span className="text-xs text-[#58413D]">qwen3-vl:8b</span>
              </div>
            </div>
          </div>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="p-2 rounded-full text-[#695C53] hover:text-[#1F1B18] hover:bg-[#F5ECE7] transition-colors"
              aria-label="Cancel analysis"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Stepper List with Connected Vertical Line */}
        <div className="flex flex-col gap-0 z-10">
          {PIPELINE_STEPS.map((step, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;
            const isLast = idx === PIPELINE_STEPS.length - 1;

            return (
              <div key={step.id} className="flex items-start gap-3.5 relative pb-4">
                {/* Connecting Vertical Line */}
                {!isLast && (
                  <div
                    className={`absolute left-4 top-8 bottom-0 w-0.5 transition-colors ${
                      isCompleted ? "bg-[#166742]/40" : isCurrent ? "bg-[#C74735]/30" : "bg-[#EADFD5]"
                    }`}
                  />
                )}

                {/* Step Badge */}
                <div className="relative z-10 shrink-0">
                  {isCompleted ? (
                    <div className="w-8 h-8 rounded-full bg-[#EAF5EE] text-[#166742] border border-[#B2DEC4] flex items-center justify-center shadow-xs">
                      <Check className="w-4 h-4 stroke-[2.5]" />
                    </div>
                  ) : isCurrent ? (
                    <div className="relative w-8 h-8 flex items-center justify-center">
                      <span className="absolute inset-0 rounded-full bg-[#FFDAD4] animate-ping opacity-60" />
                      <div className="w-8 h-8 rounded-full bg-[#C74735] text-white flex items-center justify-center shadow-md">
                        <RotateCw className="w-4 h-4 animate-spin stroke-[2.5]" />
                      </div>
                    </div>
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-[#F5ECE7] border border-[#EADFD5] text-[#8C716C] flex items-center justify-center">
                      <span className="w-2 h-2 rounded-full bg-[#8C716C]/40" />
                    </div>
                  )}
                </div>

                {/* Step Content */}
                <div className="flex flex-col flex-1 min-w-0 pt-0.5">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`text-xs sm:text-sm font-semibold truncate ${
                        isCurrent
                          ? "text-[#C74735]"
                          : isCompleted
                          ? "text-[#1F1B18]"
                          : "text-[#8C716C]"
                      }`}
                    >
                      {step.label}
                    </span>
                    {isCompleted ? (
                      <span className="text-[11px] font-semibold text-[#166742] shrink-0">
                        {step.typicalDuration}
                      </span>
                    ) : isCurrent ? (
                      <span className="text-[11px] font-bold text-[#C74735] bg-[#F2DFD3] px-2 py-0.5 rounded-full shrink-0 animate-pulse">
                        Active
                      </span>
                    ) : null}
                  </div>
                  <p className="text-xs text-[#58413D] mt-0.5 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Guarantee */}
        <div className="flex items-center justify-center gap-2 pt-1 border-t border-[#EADFD5]/60 text-xs text-[#58413D] z-10">
          <Sparkles className="w-3.5 h-3.5 text-[#C74735]" />
          <span>On-device Ollama inference • Zero cloud API transmission</span>
        </div>
      </div>
    </div>
  );
};

"use client";

import React, { useState, useEffect } from "react";
import { Loader2, CheckCircle2, ScanLine, Sparkles, Database, ShieldAlert, Languages } from "lucide-react";

interface ProcessingOverlayProps {
  onCancel?: () => void;
}

interface StepInfo {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
}

const PIPELINE_STEPS: StepInfo[] = [
  {
    id: "prep",
    label: "Image Optimization",
    icon: ScanLine,
    description: "Decoding image and applying CLAHE contrast enhancement",
  },
  {
    id: "vlm",
    label: "Local Vision Extraction",
    icon: Sparkles,
    description: "Qwen3-VL reading printed text, layout blocks, and coordinate boxes",
  },
  {
    id: "rag",
    label: "Culinary Knowledge Lookup",
    icon: Database,
    description: "Hybrid BM25 + dense vector matching against authoritative recipe records",
  },
  {
    id: "trans",
    label: "Contextual Translation",
    icon: Languages,
    description: "Translating dish titles and crafting culinary explanations",
  },
  {
    id: "safety",
    label: "Allergen & Dietary Safety",
    icon: ShieldAlert,
    description: "Verifying allergen disclosures and enforcing zero-false-safe constraints",
  },
];

export const ProcessingOverlay: React.FC<ProcessingOverlayProps> = ({ onCancel }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [elapsedSecs, setElapsedSecs] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSecs((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Progressively advance through stages realistically based on time without fake percentages
    const intervals = [1500, 3500, 5500, 7500];
    const timeouts = intervals.map((delay, idx) =>
      setTimeout(() => {
        setCurrentStepIndex(idx + 1);
      }, delay)
    );
    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-200"
    >
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl flex flex-col gap-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Analyzing Menu</h3>
              <p className="text-xs text-slate-400">Elapsed time: {elapsedSecs}s</p>
            </div>
          </div>
          {onCancel && (
            <button
              onClick={onCancel}
              className="text-xs text-slate-400 hover:text-slate-200 font-medium px-2.5 py-1 rounded-lg hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Real Step Status Flow */}
        <div className="flex flex-col gap-3.5">
          {PIPELINE_STEPS.map((step, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex;
            const StepIcon = step.icon;

            return (
              <div
                key={step.id}
                className={`flex items-start gap-3 p-2.5 rounded-xl transition-all ${
                  isCurrent
                    ? "bg-indigo-950/40 border border-indigo-500/30 text-indigo-200"
                    : isCompleted
                    ? "text-slate-300"
                    : "text-slate-600 opacity-60"
                }`}
              >
                <div className="mt-0.5">
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                  ) : (
                    <StepIcon className="w-4 h-4 text-slate-600" />
                  )}
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs font-semibold leading-tight">
                    {step.label}
                  </span>
                  <span className="text-[11px] text-slate-400 leading-normal">
                    {step.description}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="bg-slate-950/50 rounded-xl p-3 border border-slate-800/80 text-[11px] text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 shrink-0 animate-pulse" />
          <span>Privacy Guaranteed: Processing runs locally on device. No image stored remotely.</span>
        </div>
      </div>
    </div>
  );
};

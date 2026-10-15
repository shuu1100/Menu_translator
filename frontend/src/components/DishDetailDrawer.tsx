"use client";

import React, { useEffect } from "react";
import { AnalyzedDish } from "../types/menu";
import {
  X,
  ShieldAlert,
  ChevronLeft,
  ChevronRight,
  Info,
  Sparkles,
  Utensils,
  AlertTriangle,
  Volume2,
} from "lucide-react";

interface DishDetailDrawerProps {
  dish: AnalyzedDish | null;
  onClose: () => void;
  onNextDish?: () => void;
  onPrevDish?: () => void;
  hasNext?: boolean;
  hasPrev?: boolean;
}

export const DishDetailDrawer: React.FC<DishDetailDrawerProps> = ({
  dish,
  onClose,
  onNextDish,
  onPrevDish,
  hasNext = false,
  hasPrev = false,
}) => {
  // Listen for Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      } else if (e.key === "ArrowRight" && hasNext && onNextDish) {
        onNextDish();
      } else if (e.key === "ArrowLeft" && hasPrev && onPrevDish) {
        onPrevDish();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, onNextDish, onPrevDish, hasNext, hasPrev]);

  if (!dish) return null;

  const playPronunciation = () => {
    if ("speechSynthesis" in window) {
      const utterance = new SpeechSynthesisUtterance(dish.original_text);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dish-title"
      className="fixed inset-x-0 bottom-0 z-40 sm:inset-y-0 sm:right-0 sm:left-auto sm:w-[480px] bg-slate-900 border-t sm:border-t-0 sm:border-l border-slate-800 shadow-2xl flex flex-col max-h-[85vh] sm:max-h-screen animate-in slide-in-from-bottom sm:slide-in-from-right duration-200"
    >
      {/* Drawer Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/95 sticky top-0 z-10 backdrop-blur-md">
        <div className="flex items-center gap-2">
          {dish.section && (
            <span className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
              {dish.section}
            </span>
          )}
          <span className="text-xs font-semibold text-slate-400">
            Dish #{dish.reading_order}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {hasPrev && (
            <button
              type="button"
              onClick={onPrevDish}
              title="Previous Dish"
              aria-label="Previous dish in reading order"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          )}
          {hasNext && (
            <button
              type="button"
              onClick={onNextDish}
              title="Next Dish"
              aria-label="Next dish in reading order"
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dish details"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-6 text-slate-200">
        {/* Title & Native Text */}
        <div className="flex flex-col gap-1.5">
          <div className="flex items-baseline justify-between gap-3">
            <h2 id="dish-title" className="text-xl font-bold text-white tracking-tight leading-snug">
              {dish.translated_title || dish.original_text}
            </h2>
            {dish.price && (
              <span className="text-lg font-extrabold text-amber-400 shrink-0 font-mono">
                {dish.price}
              </span>
            )}
          </div>

          {/* Verbatim native script */}
          <div className="flex items-center gap-2 text-slate-400 text-sm italic">
            <span>{dish.original_text}</span>
            {typeof window !== "undefined" && "speechSynthesis" in window && (
              <button
                type="button"
                onClick={playPronunciation}
                title="Listen to pronunciation"
                className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-indigo-400 transition-colors"
              >
                <Volume2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Phonetic Pronunciation Guide */}
          {dish.phonetic_transcription && (
            <div className="inline-flex items-center gap-1.5 text-xs text-indigo-300 font-mono bg-indigo-950/40 px-2.5 py-1 rounded-lg border border-indigo-500/20 w-fit">
              <span>🗣️ Pronounce:</span>
              <span className="font-semibold">{dish.phonetic_transcription}</span>
            </div>
          )}
        </div>

        {/* Culinary Description & Context */}
        {dish.culinary_description && (
          <div className="flex flex-col gap-1.5 p-3.5 rounded-2xl bg-slate-950/50 border border-slate-800/80">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Utensils className="w-3.5 h-3.5 text-indigo-400" />
              Culinary Context
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {dish.culinary_description}
            </p>
          </div>
        )}

        {/* Flavor Profile */}
        {dish.flavor_profile && (
          <div className="flex flex-col gap-1.5">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              Flavor Notes
            </h4>
            <p className="text-xs text-slate-300 font-medium italic">
              &ldquo;{dish.flavor_profile}&rdquo;
            </p>
          </div>
        )}

        {/* Key Ingredients */}
        {dish.key_ingredients && dish.key_ingredients.length > 0 && (
          <div className="flex flex-col gap-2">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Ingredients
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {dish.key_ingredients.map((ing, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-lg text-xs bg-slate-800/80 border border-slate-700/60 text-slate-300"
                >
                  {ing}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Evidence-Backed Allergen Disclosures */}
        <div className="flex flex-col gap-2.5">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            Allergen Evidence & Warnings
          </h4>

          {dish.allergen_warnings.length > 0 ? (
            <div className="flex flex-col gap-2">
              {dish.allergen_warnings.map((w, idx) => {
                const isConfirmed = w.status === "confirmed";
                const isPossible = w.status === "possible";

                return (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl border flex flex-col gap-1 ${
                      isConfirmed
                        ? "bg-rose-500/10 border-rose-500/30 text-rose-200"
                        : isPossible
                        ? "bg-amber-500/10 border-amber-500/30 text-amber-200"
                        : "bg-slate-800/40 border-slate-700/40 text-slate-300"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold text-xs uppercase tracking-wider">
                        {isConfirmed ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                        ) : (
                          <Info className="w-3.5 h-3.5 text-amber-400" />
                        )}
                        <span>{w.allergen}</span>
                      </div>
                      <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-slate-900 border border-slate-700">
                        {w.status} ({w.source})
                      </span>
                    </div>
                    {w.notes && (
                      <p className="text-[11px] text-slate-300 pl-5 leading-normal">
                        {w.notes}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-slate-800/40 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <Info className="w-4 h-4 text-slate-400 shrink-0" />
              <span>No explicit allergen keywords printed on menu.</span>
            </div>
          )}
        </div>

        {/* Dietary Lifestyle Compatibility */}
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Dietary Compatibility
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Vegan</span>
              <span
                className={`font-semibold uppercase text-[10px] px-2 py-0.5 rounded ${
                  dish.dietary_compatibility.vegan === "yes"
                    ? "bg-emerald-500/20 text-emerald-300"
                    : dish.dietary_compatibility.vegan === "no"
                    ? "bg-rose-500/20 text-rose-300"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {dish.dietary_compatibility.vegan}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Vegetarian</span>
              <span
                className={`font-semibold uppercase text-[10px] px-2 py-0.5 rounded ${
                  dish.dietary_compatibility.vegetarian === "yes"
                    ? "bg-emerald-500/20 text-emerald-300"
                    : dish.dietary_compatibility.vegetarian === "no"
                    ? "bg-rose-500/20 text-rose-300"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {dish.dietary_compatibility.vegetarian}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Gluten-Free</span>
              <span
                className={`font-semibold uppercase text-[10px] px-2 py-0.5 rounded ${
                  dish.dietary_compatibility.gluten_free === "yes"
                    ? "bg-emerald-500/20 text-emerald-300"
                    : dish.dietary_compatibility.gluten_free === "no"
                    ? "bg-rose-500/20 text-rose-300"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {dish.dietary_compatibility.gluten_free}
              </span>
            </div>

            <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
              <span className="text-slate-400">Halal</span>
              <span
                className={`font-semibold uppercase text-[10px] px-2 py-0.5 rounded ${
                  dish.dietary_compatibility.halal === "yes"
                    ? "bg-emerald-500/20 text-emerald-300"
                    : dish.dietary_compatibility.halal === "no"
                    ? "bg-rose-500/20 text-rose-300"
                    : "bg-slate-800 text-slate-400"
                }`}
              >
                {dish.dietary_compatibility.halal}
              </span>
            </div>
          </div>
        </div>

        {/* Mandatory Safety Notice */}
        <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-[11px] text-amber-200 flex items-start gap-2.5 mt-auto">
          <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-bold">Zero False-Safe Mandate:</span> Inferred absence of an allergen statement is <span className="underline font-semibold">never</span> proof that a dish is safe. Always verbally cross-check with kitchen staff for severe allergies.
          </p>
        </div>
      </div>
    </div>
  );
};

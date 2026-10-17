"use client";

import React, { useEffect, useSyncExternalStore, useState } from "react";
import { AnalyzedDish } from "../types/menu";
import { DishImage } from "./DishImage";
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
  CheckCircle2,
  AlertCircle,
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
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  const hasSpeech = useSyncExternalStore(
    () => () => {},
    () => typeof window !== "undefined" && "speechSynthesis" in window,
    () => false
  );

  // Keyboard accessibility
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

  const isRtl = /[\u0600-\u06ff]/.test(dish.translated_title || dish.original_text);

  const playPronunciation = () => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      setIsPlayingAudio(true);
      const textToSpeak = dish.original_text || dish.original_name || "";
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.onend = () => setIsPlayingAudio(false);
      utterance.onerror = () => setIsPlayingAudio(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="dish-title"
      className="fixed inset-x-0 bottom-0 z-40 sm:inset-y-0 sm:right-0 sm:left-auto sm:w-[480px] bg-white border-t sm:border-t-0 sm:border-l border-[#EADFD5] shadow-[0_8px_32px_rgba(41,37,34,0.12)] flex flex-col max-h-[85vh] sm:max-h-screen rounded-t-3xl sm:rounded-none sm:rounded-l-3xl animate-in slide-in-from-bottom sm:slide-in-from-right duration-200 overflow-hidden"
    >
      {/* Mobile Drawer Grab Handle */}
      <div className="w-full pt-3 pb-1 flex justify-center sm:hidden bg-white">
        <div className="w-10 h-1 bg-[#EAE1DC] rounded-full" />
      </div>

      {/* Drawer Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[#EADFD5] bg-white/95 sticky top-0 z-10 backdrop-blur-md">
        <div className="flex items-center gap-2">
          {dish.section && (
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[#F2DFD3] text-[#A52F20]">
              {dish.section}
            </span>
          )}
          <span className="text-xs font-semibold text-[#695C53]">
            Dish #{dish.reading_order}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          {hasPrev && (
            <button
              type="button"
              onClick={onPrevDish}
              title="Previous Dish"
              aria-label="Previous dish in reading order"
              className="p-2 rounded-full text-[#695C53] hover:text-[#1F1B18] hover:bg-[#F5ECE7] transition-colors"
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
              className="p-2 rounded-full text-[#695C53] hover:text-[#1F1B18] hover:bg-[#F5ECE7] transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dish details"
            className="p-2 rounded-full text-[#695C53] hover:text-[#1F1B18] hover:bg-[#F5ECE7] transition-colors ml-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Drawer Scrollable Content */}
      <div dir={isRtl ? "rtl" : "ltr"} className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-5 text-[#1F1B18]">
        {/* Prominent Representative Food Photograph */}
        <div className="w-full">
          <DishImage
            imageInfo={dish.representative_image}
            dishName={dish.translated_name || dish.translated_title || dish.original_name || dish.original_text}
            aspectRatioClass="aspect-[16/9]"
            priority={true}
            showAttribution={true}
          />
          <p className="text-[10px] text-[#70645C] mt-1.5 flex items-center gap-1 font-medium italic">
            <Info className="w-3 h-3 text-[#A52F20] shrink-0" />
            Representative photo for culinary reference. Actual restaurant presentation may vary.
          </p>
        </div>

        {/* Title, Price & Promotional Badges */}
        <div className="flex flex-col gap-2">
          <div className="flex items-start justify-between gap-3">
            <h2 id="dish-title" className="text-xl sm:text-2xl font-bold text-[#1F1B18] tracking-tight leading-snug">
              {dish.translated_name || dish.translated_title || dish.original_name || dish.original_text}
            </h2>
            {(dish.price_text_original || dish.price) && (
              <span className="text-lg sm:text-xl font-extrabold text-[#C74735] shrink-0 font-mono">
                {dish.price_currency || dish.currency ? `${dish.price_currency || dish.currency} ` : ""}{dish.price_text_original || dish.price}
              </span>
            )}
          </div>

          {/* Promotional / Signature Tags */}
          {dish.tags && dish.tags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {dish.tags.map((tag, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider bg-[#F2DFD3] text-[#A52F20] border border-[#C74735]/20"
                >
                  ⭐ {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Phonetic Pronunciation Tool Card with Audio Soundwave */}
        <div className="w-full bg-[#FBF2ED] border border-[#EADFD5] rounded-2xl p-3.5 flex items-center justify-between gap-3 shadow-xs">
          <div className="flex items-center gap-3 min-w-0">
            <button
              type="button"
              onClick={playPronunciation}
              disabled={!hasSpeech}
              title="Listen to native pronunciation"
              className="w-10 h-10 rounded-full bg-[#C74735] hover:bg-[#A93629] text-white flex items-center justify-center shadow-sm active:scale-95 transition-all shrink-0 cursor-pointer disabled:opacity-50"
            >
              <Volume2 className={`w-5 h-5 ${isPlayingAudio ? "animate-bounce" : ""}`} />
            </button>
            <div className="flex flex-col truncate">
              <span className="text-[11px] font-bold text-[#695C53] uppercase tracking-wider">
                Native Pronunciation
              </span>
              <span className="text-sm font-semibold text-[#1F1B18] truncate mt-0.5">
                {dish.transliteration || dish.phonetic_transcription
                  ? `“${dish.transliteration || dish.phonetic_transcription}”`
                  : dish.original_text || dish.original_name}
              </span>
            </div>
          </div>

          {/* Soundwave animation bars */}
          <div className="flex items-center gap-1 h-6 px-1">
            <div className={`w-1 bg-[#C74735] rounded-full transition-all ${isPlayingAudio ? "h-5 animate-pulse" : "h-2"}`} />
            <div className={`w-1 bg-[#C74735] rounded-full transition-all ${isPlayingAudio ? "h-6 animate-pulse delay-75" : "h-4"}`} />
            <div className={`w-1 bg-[#C74735] rounded-full transition-all ${isPlayingAudio ? "h-3 animate-pulse delay-150" : "h-2"}`} />
            <div className={`w-1 bg-[#C74735] rounded-full transition-all ${isPlayingAudio ? "h-5 animate-pulse delay-100" : "h-3"}`} />
          </div>
        </div>

        {/* Authentic Original Scanned Snippet */}
        <div className="w-full bg-[#F5ECE7] border border-[#EADFD5] rounded-2xl p-3.5 flex flex-col gap-1.5">
          <span className="text-[10px] uppercase font-bold text-[#695C53] tracking-wider">
            Original Scanned Menu Text:
          </span>
          <p className="text-base font-semibold text-[#1F1B18]">
            {dish.original_name || dish.original_text}
          </p>
          {dish.original_description && (
            <div className="border-t border-[#EADFD5] pt-1.5 mt-0.5">
              <span className="text-[10px] uppercase font-bold text-[#695C53] block">Printed Description:</span>
              <p className="text-xs text-[#58413D] italic mt-0.5">{dish.original_description}</p>
            </div>
          )}
        </div>

        {/* Translated Printed Description */}
        {dish.translated_description || dish.culinary_description ? (
          <div className="flex flex-col gap-1.5 p-4 rounded-2xl bg-[#FBF2ED] border border-[#EADFD5]">
            <h4 className="text-xs font-bold text-[#58413D] uppercase tracking-wider flex items-center gap-1.5">
              <Utensils className="w-3.5 h-3.5 text-[#C74735]" />
              Translated Description
            </h4>
            <p className="text-xs sm:text-sm text-[#1F1B18] leading-relaxed">
              {dish.translated_description || dish.culinary_description}
            </p>
          </div>
        ) : (
          <div className="p-3.5 rounded-xl bg-[#F5ECE7]/60 border border-[#EADFD5] text-xs text-[#695C53] italic">
            No description provided on the menu
          </div>
        )}

        {/* Optional Authoritative Cultural Context */}
        {dish.generated_description && (
          <div className="flex flex-col gap-1.5 p-4 rounded-2xl bg-[#F2DFD3]/40 border border-[#C74735]/20">
            <h4 className="text-xs font-bold text-[#A52F20] uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#C74735]" />
              Culinary Context & Recipe Notes
            </h4>
            <p className="text-xs sm:text-sm text-[#1F1B18] leading-relaxed">
              {dish.generated_description}
            </p>
          </div>
        )}

        {/* Flavor Profile */}
        {dish.flavor_profile && (
          <div className="flex flex-col gap-1 p-3 rounded-xl bg-white border border-[#EADFD5]">
            <span className="text-[10px] font-bold text-[#695C53] uppercase tracking-wider">Flavor Profile</span>
            <p className="text-xs text-[#1F1B18] font-medium italic">
              &ldquo;{dish.flavor_profile}&rdquo;
            </p>
          </div>
        )}

        {/* Verified Ingredients Breakdown */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-[#58413D] uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#166742]" />
              Ingredients
            </h4>
            {dish.ingredient_evidence_status === "confirmed" ? (
              <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#EAF5EE] text-[#166742] border border-[#B2DEC4]">
                Verified Recipe DB
              </span>
            ) : (
              <span className="text-[10px] font-medium px-2.5 py-0.5 rounded-full bg-[#F5ECE7] text-[#695C53] border border-[#EADFD5]">
                Menu Text
              </span>
            )}
          </div>

          {dish.key_ingredients && dish.key_ingredients.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {dish.key_ingredients.map((ing, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-full text-xs font-medium bg-[#F5ECE7] border border-[#EADFD5] text-[#1F1B18]"
                >
                  {ing}
                </span>
              ))}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-[#F5ECE7]/60 border border-[#EADFD5] flex items-center gap-2 text-xs text-[#695C53]">
              <Info className="w-4 h-4 text-[#8C716C] shrink-0" />
              <span>Ingredients not listed on printed menu (Unverified). Never infer ingredients or allergens from representative photos.</span>
            </div>
          )}
        </div>

        {/* Allergen Findings with Evidence */}
        <div className="flex flex-col gap-2.5">
          <h4 className="text-xs font-bold text-[#58413D] uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-[#9B6416]" />
            Dietary & Allergen Audit
          </h4>

          {dish.allergen_warnings.length > 0 ? (
            <div className="flex flex-col gap-2">
              {dish.allergen_warnings.map((w, idx) => {
                const isConfirmed = w.status === "confirmed";
                const isPossible = w.status === "possible";

                return (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-xl border flex flex-col gap-1.5 ${
                      isConfirmed
                        ? "bg-[#FFDAD6]/60 border-[#BA1A1A]/30 text-[#93000A]"
                        : isPossible
                        ? "bg-[#FCF5EB] border-[#F0D6AF] text-[#9B6416]"
                        : "bg-[#F5ECE7] border-[#EADFD5] text-[#1F1B18]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-bold text-xs uppercase tracking-wider">
                        {isConfirmed ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-[#BA1A1A]" />
                        ) : (
                          <AlertCircle className="w-3.5 h-3.5 text-[#9B6416]" />
                        )}
                        <span>{w.allergen}</span>
                      </div>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-white border border-[#EADFD5] text-[#1F1B18]">
                        {w.status}
                      </span>
                    </div>
                    {w.notes && (
                      <p className="text-xs text-[#58413D] pl-5 leading-relaxed">
                        {w.notes}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-3 rounded-xl bg-[#FCF5EB] border border-[#F0D6AF] text-xs text-[#9B6416] flex items-start gap-2 font-medium">
              <AlertCircle className="w-4 h-4 text-[#9B6416] shrink-0 mt-0.5" />
              <span>No allergen information found on printed menu. Inferred absence is never proof of safety — please confirm with restaurant staff.</span>
            </div>
          )}
        </div>

        {/* Dietary Lifestyle Compatibility Grid */}
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-bold text-[#58413D] uppercase tracking-wider">
            Dietary Lifestyle Compatibility
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { label: "Vegan", val: dish.dietary_compatibility.vegan },
              { label: "Vegetarian", val: dish.dietary_compatibility.vegetarian },
              { label: "Gluten-Free", val: dish.dietary_compatibility.gluten_free },
              { label: "Halal", val: dish.dietary_compatibility.halal },
            ].map(({ label, val }) => (
              <div
                key={label}
                className="p-3 rounded-xl bg-[#FBF2ED] border border-[#EADFD5] flex items-center justify-between"
              >
                <span className="font-semibold text-[#58413D]">{label}</span>
                <span
                  className={`font-bold uppercase text-[10px] px-2 py-0.5 rounded-full ${
                    val === "yes"
                      ? "bg-[#EAF5EE] text-[#166742] border border-[#B2DEC4]"
                      : val === "no"
                      ? "bg-[#FFDAD6] text-[#93000A] border border-[#BA1A1A]/30"
                      : "bg-[#F5ECE7] text-[#695C53] border border-[#EADFD5]"
                  }`}
                >
                  {val === "yes" ? "Verified Yes" : val === "no" ? "Non-Compliant" : "Unverified"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Mandatory Safety Notice */}
        <div className="p-4 rounded-2xl bg-[#FCF5EB] border border-[#F0D6AF] text-xs text-[#9B6416] flex items-start gap-3 mt-auto shadow-xs">
          <ShieldAlert className="w-4 h-4 text-[#9B6416] shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <span className="font-bold">Zero False-Safe Guarantee:</span> Inferred absence of an allergen statement on a physical menu is <span className="underline font-semibold">never</span> proof of food safety. Confirm all allergens with kitchen staff.
          </p>
        </div>
      </div>
    </div>
  );
};

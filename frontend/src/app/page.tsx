"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Camera,
  Upload,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  UtensilsCrossed,
  ArrowRight,
  ArrowLeft,
  RotateCw,
  Search,
  Globe,
  FileText,
  Image as ImageIcon,
  ChevronRight,
  ShieldAlert,
  Activity,
  Zap,
  ChevronDown,
  ChevronUp,
  Store,
  Layers,
  Lock,
  Volume2,
} from "lucide-react";
import {
  AnalyzedDish,
  MenuAnalysisResponse,
  SupportedLanguage,
} from "../types/menu";
import { LanguageSelector } from "../components/LanguageSelector";
import { DietaryPreferencesSelector } from "../components/DietaryPreferencesSelector";
import { CameraCaptureModal } from "../components/CameraCaptureModal";
import { ProcessingOverlay } from "../components/ProcessingOverlay";
import { MenuCanvasOverlay } from "../components/MenuCanvasOverlay";
import { DishDetailDrawer } from "../components/DishDetailDrawer";
import { DishImage } from "../components/DishImage";
import { OfflineBanner } from "../components/OfflineBanner";
import { SAMPLE_MENUS } from "../data/sample_menus";
import { apiClient } from "../services/apiClient";
import { useTranslation } from "../i18n/I18nContext";
import {
  ACCEPTED_IMAGE_TYPES,
  ACCEPTED_IMAGE_MIMES,
  MAX_UPLOAD_SIZE_BYTES,
  MAX_UPLOAD_SIZE_MB,
} from "../constants/upload";

interface ServiceInfo {
  status: "ok" | "healthy" | "degraded" | "error" | "offline";
  message: string;
}

interface HealthData {
  status: string;
  app_name: string;
  version: string;
  services: {
    api?: ServiceInfo;
    database?: ServiceInfo;
    model_service?: ServiceInfo;
  };
}

export default function Home() {
  const { t, uiLanguage, setUiLanguage, isRtl } = useTranslation();

  // Navigation & Screen state
  const [activeScreen, setActiveScreen] = useState<"capture" | "results">("capture");
  const [targetLanguage, setTargetLanguage] = useState<SupportedLanguage>("en");
  const [userRestrictions, setUserRestrictions] = useState<string[]>(["gluten", "dairy"]);

  // Camera & Upload state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [rotation, setRotation] = useState<number>(0);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pendingPreviewUrl, setPendingPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Analysis result state
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<MenuAnalysisResponse | null>(null);
  const [selectedDish, setSelectedDish] = useState<AnalyzedDish | null>(null);

  // Results View Tabs & Filters
  const [resultsTab, setResultsTab] = useState<"menu" | "overlay">("menu");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedSection, setSelectedSection] = useState<string>("all");
  const [isRetranslating, setIsRetranslating] = useState<boolean>(false);
  const [showPerformanceMetrics, setShowPerformanceMetrics] = useState<boolean>(false);

  // Backend Health state
  const [health, setHealth] = useState<HealthData | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await apiClient.getHealth();
      setHealth(data as HealthData);
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const initCheck = async () => {
      try {
        const data = await apiClient.getHealth();
        if (active) setHealth(data as HealthData);
      } catch {
        if (active) setHealth(null);
      }
    };
    initCheck();
    return () => {
      active = false;
    };
  }, []);

  // Load sample demo menu
  const handleLoadSampleMenu = (sampleId: string) => {
    const sample = SAMPLE_MENUS.find((s) => s.id === sampleId) || SAMPLE_MENUS[0];
    setCurrentImageUrl(sample.imageUrl);
    setAnalysisResult(sample.data);
    setSelectedDish(sample.data.dishes[0] || null);
    setActiveScreen("results");
    setErrorMessage(null);
  };

  const [abortController, setAbortController] = useState<AbortController | null>(null);

  // Analyze uploaded or captured image via backend API
  const handleAnalyzeMenuImage = async (file: File, rotationDeg: number = rotation) => {
    if (!file) return;

    // If an existing request is running, abort it cleanly so the newly selected image can proceed
    if (abortController) {
      abortController.abort();
    }

    // Validate supported image MIME types and extensions
    const fileMime = file.type ? file.type.toLowerCase() : "";
    const fileExt = file.name ? file.name.split(".").pop()?.toLowerCase() : "";
    const isMimeValid = ACCEPTED_IMAGE_MIMES.includes(fileMime as typeof ACCEPTED_IMAGE_MIMES[number]);
    const isExtValid = ["jpg", "jpeg", "png", "webp", "mpo", "jfif", "pjpeg", "avif", "bmp"].includes(fileExt || "");

    if (!isMimeValid && !isExtValid) {
      setErrorMessage(
        `Unsupported file type '${file.type || fileExt || "unknown"}'. Please upload a JPEG, PNG, or WebP photo.`
      );
      return;
    }

    // Validate file size limit
    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      const sizeMb = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(
        `File is too large (${sizeMb} MB). Maximum allowed upload size is ${MAX_UPLOAD_SIZE_MB} MB.`
      );
      return;
    }

    // Ensure valid MIME type for FormData if missing from browser File object
    let uploadFile = file;
    if (!file.type && isExtValid) {
      const mimeMap: Record<string, string> = {
        jpg: "image/jpeg",
        jpeg: "image/jpeg",
        jfif: "image/jpeg",
        pjpeg: "image/jpeg",
        png: "image/png",
        webp: "image/webp",
        mpo: "image/mpo",
        avif: "image/avif",
        bmp: "image/bmp",
      };
      uploadFile = new File([file], file.name, { type: mimeMap[fileExt!] || "image/jpeg" });
    }

    const controller = new AbortController();
    setAbortController(controller);
    setIsProcessing(true);
    setErrorMessage(null);

    const objectUrl = URL.createObjectURL(uploadFile);
    setCurrentImageUrl(objectUrl);
    setPendingPreviewUrl(objectUrl);
    setPendingFile(uploadFile);

    try {
      const result = await apiClient.analyzeMenu({
        file: uploadFile,
        targetLanguage,
        dietaryRestrictions: userRestrictions,
        rotation: rotationDeg,
        signal: controller.signal,
      });

      setAnalysisResult(result);
      if (result.dishes.length === 0) {
        setErrorMessage(
          result.menu_metadata.warnings?.[0]?.message ||
            "No legible dishes could be extracted from this photo. Ensure the menu is clearly lit and in focus."
        );
      }
      setSelectedDish(result.dishes[0] || null);
      setResultsTab("menu");
      setActiveScreen("results");
    } catch (err: unknown) {
      if ((err as { name?: string })?.name === "AbortError") {
        setErrorMessage("Menu analysis was cancelled.");
        return;
      }
      const apiErr = err as { code?: string; message?: string; status?: number };
      let friendlyMsg = apiErr.message || (err instanceof Error ? err.message : "Failed to analyze menu.");

      if (apiErr.code === "PIPELINE_TIMEOUT" || apiErr.code === "INFERENCE_TIMEOUT" || apiErr.status === 504) {
        friendlyMsg = "Analysis timed out: the local model took too long to process this image. Try orienting the photo upright or using a clearer menu shot.";
      } else if (apiErr.code === "MODEL_SERVICE_UNAVAILABLE" || apiErr.status === 503) {
        friendlyMsg = "Local AI vision model service is unavailable. Please verify Ollama is running ('ollama serve').";
      } else if (apiErr.code === "PAYLOAD_TOO_LARGE" || apiErr.status === 413) {
        friendlyMsg = "The uploaded menu photo is too large. Please upload an image under 15 MB.";
      } else if (apiErr.code === "INVALID_IMAGE" || apiErr.status === 400) {
        friendlyMsg = "Could not decode image. Please provide a valid JPEG, PNG, or WebP menu photo.";
      } else if (apiErr.code === "NETWORK_ERROR" || apiErr.status === 0) {
        friendlyMsg = "Cannot reach Menu Translator backend on port 8001. Please verify the backend service is running.";
      }

      setErrorMessage(
        `${friendlyMsg} (Tip: You can also explore pre-loaded demo menus below without live inference).`
      );
    } finally {
      setIsProcessing(false);
      setAbortController(null);
    }
  };

  const handleRetranslate = async (newLang: SupportedLanguage) => {
    if (!analysisResult || analysisResult.dishes.length === 0 || isRetranslating) return;
    setIsRetranslating(true);
    setTargetLanguage(newLang);
    try {
      const resp = await apiClient.retranslateMenu({
        dishes: analysisResult.dishes,
        targetLanguage: newLang,
        userRestrictions,
      });

      // Preserve existing matched images across dishes using stable dish_id
      const imageMap = new Map(
        analysisResult.dishes.map((d) => [d.dish_id, d.representative_image])
      );
      const updatedDishes = resp.dishes.map((d) => ({
        ...d,
        representative_image: imageMap.get(d.dish_id) || d.representative_image || null,
      }));

      setAnalysisResult({
        ...analysisResult,
        dishes: updatedDishes,
        menu_metadata: {
          ...analysisResult.menu_metadata,
          target_language: newLang,
        },
      });
      if (selectedDish) {
        const updated = updatedDishes.find((d) => d.dish_id === selectedDish.dish_id);
        if (updated) setSelectedDish(updated);
      }
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ||
        (err instanceof Error ? err.message : "Retranslation failed.");
      setErrorMessage(msg);
    } finally {
      setIsRetranslating(false);
    }
  };

  // Asynchronous non-blocking food image lookup for extracted dishes
  useEffect(() => {
    if (!analysisResult || analysisResult.dishes.length === 0) return;

    // Check if any dishes are missing a representative image
    const dishesNeedingImages = analysisResult.dishes.filter((d) => !d.representative_image);
    if (dishesNeedingImages.length === 0) return;

    const controller = new AbortController();

    const fetchImages = async () => {
      try {
        const payload = dishesNeedingImages.map((d) => ({
          dish_id: d.dish_id,
          dish_name: d.translated_name || d.translated_title || d.original_name || d.original_text,
          native_name: d.original_name || d.original_text,
          transliteration: d.transliteration || d.phonetic_transcription,
          cuisine: analysisResult.menu_metadata?.source_language || undefined,
          section: d.section || undefined,
          ingredients: d.key_ingredients || [],
        }));

        const response = await apiClient.batchSearchDishImages({
          dishes: payload,
          signal: controller.signal,
        });

        // Merge images into current dishes without disrupting user view
        setAnalysisResult((prev) => {
          if (!prev) return null;
          const updated = prev.dishes.map((d) => {
            const matchedImg = response.results[d.dish_id];
            if (matchedImg) {
              return { ...d, representative_image: matchedImg };
            }
            return d;
          });
          return { ...prev, dishes: updated };
        });

        // Also update selected dish if drawer is currently open
        setSelectedDish((prevSelected) => {
          if (!prevSelected) return null;
          const matchedImg = response.results[prevSelected.dish_id];
          if (matchedImg) {
            return { ...prevSelected, representative_image: matchedImg };
          }
          return prevSelected;
        });
      } catch (err: unknown) {
        if ((err as { name?: string })?.name === "AbortError") return;
        // Non-blocking: failure to load external photos does not impact OCR / translations
        console.warn("Background food image search encountered an error:", err);
      }
    };

    fetchImages();

    return () => {
      controller.abort();
    };
  }, [analysisResult?.processing_metadata?.request_id, analysisResult?.dishes.length]);

  // Single dish image retry handler
  const handleRetryDishImage = async (dishId: string) => {
    if (!analysisResult) return;
    const targetDish = analysisResult.dishes.find((d) => d.dish_id === dishId);
    if (!targetDish) return;

    try {
      const img = await apiClient.searchDishImage({
        dishId,
        dishName: targetDish.translated_name || targetDish.translated_title || targetDish.original_name || targetDish.original_text,
        nativeName: targetDish.original_name || targetDish.original_text,
        transliteration: targetDish.transliteration || targetDish.phonetic_transcription || undefined,
        section: targetDish.section || undefined,
      });

      setAnalysisResult((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          dishes: prev.dishes.map((d) => (d.dish_id === dishId ? { ...d, representative_image: img } : d)),
        };
      });

      setSelectedDish((prev) => {
        if (prev && prev.dish_id === dishId) {
          return { ...prev, representative_image: img };
        }
        return prev;
      });
    } catch (e) {
      console.warn("Failed to retry dish image:", e);
    }
  };

  const handleFileSelect = (file: File) => {
    if (!file) return;
    handleAnalyzeMenuImage(file, rotation);
  };

  const handleCancelProcessing = () => {
    if (abortController) {
      abortController.abort();
    }
    setIsProcessing(false);
    setAbortController(null);
  };

  // Handlers for Next / Prev dish navigation in drawer
  const dishes = analysisResult?.dishes || [];
  const currentDishIndex = selectedDish
    ? dishes.findIndex((d) => d.dish_id === selectedDish.dish_id)
    : -1;

  const handleNextDish = () => {
    if (currentDishIndex >= 0 && currentDishIndex < dishes.length - 1) {
      setSelectedDish(dishes[currentDishIndex + 1]);
    }
  };

  const handlePrevDish = () => {
    if (currentDishIndex > 0) {
      setSelectedDish(dishes[currentDishIndex - 1]);
    }
  };

  const handleReset = () => {
    setActiveScreen("capture");
    setSelectedDish(null);
    setAnalysisResult(null);
    setCurrentImageUrl(null);
    setErrorMessage(null);
    setPendingFile(null);
    setPendingPreviewUrl(null);
    setRotation(0);
  };

  return (
    <div className="min-h-screen bg-[#FFF8F5] text-[#1F1B18] flex flex-col selection:bg-[#F2DFD3] selection:text-[#A52F20]">
      {/* Offline / Service Status Banner */}
      <OfflineBanner
        backendReachable={health !== null}
        modelReady={
          health?.services.model_service?.status === "healthy" ||
          health?.services.model_service?.status === "ok"
        }
        onRefresh={fetchHealth}
      />

      {/* Main Top Navigation Header (Warm Epicurean Glassmorphism) */}
      <header className="sticky top-0 z-30 bg-[#FFF8F5]/90 backdrop-blur-xl border-b border-[#EADFD5] shadow-[0_1px_8px_rgba(41,37,34,0.04)] px-4 sm:px-8 py-3.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#C74735] flex items-center justify-center shadow-md shadow-[#C74735]/25 shrink-0 text-white">
            <UtensilsCrossed className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-[#1F1B18] flex items-center gap-2">
              {t("header.title")}
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-[#EAF5EE] text-[#166742] border border-[#B2DEC4]">
                {t("header.badge")}
              </span>
            </h1>
            <p className="text-[11px] text-[#70645C] hidden sm:block">
              {t("header.subtitle")}
            </p>
          </div>
        </div>

        {/* Global Controls: Website Language & Menu Target Language */}
        <div className="flex items-center gap-2 sm:gap-3 flex-wrap justify-end">
          <LanguageSelector
            value={uiLanguage}
            onChange={setUiLanguage}
            label={t("header.uiLanguage")}
            iconType="globe"
          />
          <LanguageSelector
            value={targetLanguage}
            onChange={(newLang) => {
              setTargetLanguage(newLang);
              if (activeScreen === "results" && analysisResult && analysisResult.dishes.length > 0) {
                handleRetranslate(newLang);
              }
            }}
            label={t("header.targetLanguage")}
            iconType="translate"
          />

          {activeScreen === "results" && (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsCameraOpen(true)}
                title="Scan another menu with camera"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full bg-[#C74735] hover:bg-[#A52F20] text-xs font-bold text-white transition-all cursor-pointer shadow-sm active:scale-95"
              >
                <Camera className="w-3.5 h-3.5 text-white" />
                <span className="hidden sm:inline">{t("header.scan")}</span>
              </button>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                title="Upload another menu photo"
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full bg-[#FBF2ED] hover:bg-[#F2DFD3] border border-[#EADFD5] text-xs font-bold text-[#1F1B18] transition-all cursor-pointer shadow-sm active:scale-95"
              >
                <Upload className="w-3.5 h-3.5 text-[#C74735]" />
                <span className="hidden sm:inline">{t("header.upload")}</span>
              </button>
              <button
                type="button"
                onClick={handleReset}
                title="Return to home screen"
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#FFFFFF] hover:bg-[#FBF2ED] border border-[#EADFD5] text-xs font-bold text-[#70645C] hover:text-[#1F1B18] transition-all cursor-pointer shadow-sm active:scale-95"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{t("header.reset")}</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* App Body */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-8">
        {/* Error Alert if encountered */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-[#FCF5EB] border border-[#F0D6AF] text-[#9B6416] text-xs flex items-center justify-between gap-3 animate-in fade-in shadow-sm">
            <div className="flex items-start gap-2.5 min-w-0">
              <AlertCircle className="w-4 h-4 text-[#9B6416] shrink-0 mt-0.5" />
              <p className="leading-relaxed font-medium">{errorMessage}</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {pendingFile && (
                <button
                  type="button"
                  onClick={() => handleAnalyzeMenuImage(pendingFile, rotation)}
                  className="px-3 py-1.5 rounded-xl bg-[#C74735] hover:bg-[#A52F20] text-white text-xs font-bold transition-all shadow-sm cursor-pointer"
                >
                  {t("errors.retryAnalysis")}
                </button>
              )}
              <button
                onClick={() => setErrorMessage(null)}
                className="text-[#9B6416] hover:text-[#1F1B18] font-bold text-sm cursor-pointer px-1"
                aria-label={t("errors.dismiss")}
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* SCREEN 1: LANDING & CAPTURE */}
        {activeScreen === "capture" && (
          <div className="flex flex-col gap-10 w-full animate-in fade-in">
            {/* HERO SECTION: Two-column responsive layout */}
            <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center pt-2">
              {/* Left Column: Editorial Headline & Actions */}
              <div className="lg:col-span-7 flex flex-col gap-5">
                <div className="inline-flex items-center gap-2 self-start px-3.5 py-1.5 rounded-full bg-[#F2DFD3] text-[#A52F20] text-xs font-bold border border-[#EADFD5]/60 shadow-xs">
                  <Sparkles className="w-3.5 h-3.5 text-[#C74735]" />
                  <span>{t("hero.pill")}</span>
                </div>

                <h2 className="text-3xl sm:text-5xl font-extrabold text-[#1F1B18] tracking-tight leading-[1.15]">
                  {t("hero.headingPrefix")} <br className="hidden sm:inline" />
                  <span className="text-[#C74735]">{t("hero.headingHighlight")}</span>
                </h2>

                <p className="text-sm sm:text-base text-[#70645C] leading-relaxed max-w-xl">
                  {t("hero.description")}
                </p>

                {/* Primary & Secondary Call to Actions */}
                <div className="flex flex-col sm:flex-row items-center gap-3.5 pt-1">
                  <button
                    type="button"
                    disabled={isProcessing}
                    onClick={() => setIsCameraOpen(true)}
                    className={`w-full sm:w-auto px-6 h-13 rounded-2xl bg-[#C74735] hover:bg-[#A52F20] text-white font-bold text-sm flex items-center justify-center gap-2.5 shadow-lg shadow-[#C74735]/25 active:scale-[0.98] transition-all cursor-pointer ${
                      isProcessing ? "opacity-50 cursor-not-allowed pointer-events-none" : ""
                    }`}
                  >
                    <Camera className="w-5 h-5 text-white" />
                    <span>{t("hero.scanButton")}</span>
                  </button>

                  <label
                    htmlFor="menu-photo-upload"
                    role="button"
                    tabIndex={isProcessing ? -1 : 0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        fileInputRef.current?.click();
                      }
                    }}
                    className={`w-full sm:w-auto px-6 h-13 rounded-2xl bg-[#FFFFFF] hover:bg-[#FBF2ED] text-[#1F1B18] font-bold text-sm border border-[#EADFD5] flex items-center justify-center gap-2.5 active:scale-[0.98] transition-all shadow-sm cursor-pointer select-none ${
                      isProcessing ? "opacity-50 cursor-not-allowed pointer-events-none" : ""
                    }`}
                  >
                    <Upload className="w-5 h-5 text-[#C74735] pointer-events-none" />
                    <span className="pointer-events-none">{isProcessing ? t("hero.analyzingButton") : t("hero.uploadButton")}</span>
                    <input
                      ref={fileInputRef}
                      id="menu-photo-upload"
                      type="file"
                      accept={ACCEPTED_IMAGE_TYPES}
                      disabled={isProcessing}
                      className="sr-only"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFileSelect(file);
                        e.target.value = "";
                      }}
                    />
                  </label>

                  {/* Orientation Adjustment Button */}
                  <button
                    type="button"
                    disabled={isProcessing}
                    onClick={() => setRotation((r) => (r + 90) % 360)}
                    className="w-full sm:w-auto px-4 h-13 rounded-2xl bg-[#FFFFFF] hover:bg-[#FBF2ED] text-[#70645C] hover:text-[#1F1B18] font-semibold text-xs border border-[#EADFD5] flex items-center justify-center gap-2 active:scale-[0.98] transition-all shadow-sm cursor-pointer"
                    title={t("hero.rotateTooltip")}
                  >
                    <RotateCw className="w-4 h-4 text-[#C74735]" />
                    <span>{t("hero.rotateButton", { rotation })}</span>
                  </button>
                </div>

                {/* Privacy Badge */}
                <div className="flex items-center gap-2 text-xs text-[#70645C] pt-1">
                  <Lock className="w-3.5 h-3.5 text-[#C74735] shrink-0" />
                  <span>{t("hero.privacyBadge")}</span>
                </div>
              </div>

              {/* Right Column: Appetizing Food Photography Composition */}
              <div className="lg:col-span-5 relative">
                <div className="relative rounded-3xl overflow-hidden border border-[#EADFD5] shadow-xl bg-[#F5ECE7] group">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="https://images.unsplash.com/photo-1569718212165-3a8278d5f624?auto=format&fit=crop&w=1000&q=80"
                    alt="Artisanal Japanese Ramen"
                    className="w-full h-80 object-cover group-hover:scale-105 transition-transform duration-700"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = SAMPLE_MENUS[0].imageUrl;
                    }}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-[#1F1B18]/85 via-[#1F1B18]/30 to-transparent" />

                  {/* Top Floating Badge */}
                  <div className="absolute top-3.5 left-3.5 right-3.5 flex items-center justify-between">
                    <div className="backdrop-blur-md bg-[#FFF8F5]/90 px-3 py-1 rounded-full flex items-center gap-2 shadow-sm border border-[#EADFD5]">
                      <span className="w-2 h-2 rounded-full bg-[#166742] animate-pulse" />
                      <span className="text-[11px] font-bold text-[#1F1B18] tracking-wide">
                        Live Multilingual OCR
                      </span>
                    </div>
                    <span className="bg-[#C74735] text-white px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider shadow-sm">
                      40+ Cuisines
                    </span>
                  </div>
                </div>
              </div>
            </section>

            {/* EXPLORE DEMO MENUS: 6-Card Responsive Grid */}
            <section className="flex flex-col gap-5 pt-2">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
                <div>
                  <div className="text-xs font-extrabold uppercase tracking-widest text-[#C74735] mb-1">
                    {t("demos.tag")}
                  </div>
                  <h3 className="text-xl sm:text-2xl font-extrabold text-[#1F1B18] tracking-tight">
                    {t("demos.title")}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#70645C] mt-0.5">
                    {t("demos.description")}
                  </p>
                </div>
                <div className="text-xs font-semibold text-[#70645C] bg-[#F2DFD3] px-3 py-1.5 rounded-full border border-[#EADFD5] self-start sm:self-auto shrink-0">
                  {t("demos.cuisinesBadge")}
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {SAMPLE_MENUS.map((sample) => (
                  <div
                    key={sample.id}
                    onClick={() => handleLoadSampleMenu(sample.id)}
                    className="bg-[#FFFFFF] rounded-2xl border border-[#EADFD5] overflow-hidden shadow-sm hover:shadow-xl hover:border-[#C74735]/40 transition-all duration-300 flex flex-col justify-between cursor-pointer group"
                  >
                    {/* Food Photo with Overlay Badges */}
                    <div className="relative h-44 w-full overflow-hidden bg-[#F5ECE7]">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img
                        src={sample.photoUrl}
                        alt={sample.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        onError={(e) => {
                          // Fallback to SVG menu image if network image fails
                          (e.target as HTMLImageElement).src = sample.imageUrl;
                        }}
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-[#1F1B18]/70 via-transparent to-black/20" />

                      {/* Top Badges */}
                      <div className="absolute top-3 left-3 right-3 flex items-center justify-between">
                        <span className="px-2.5 py-1 rounded-full bg-[#FFF8F5]/90 backdrop-blur-md text-[11px] font-bold text-[#1F1B18] shadow-sm border border-[#EADFD5]">
                          {sample.cuisine}
                        </span>
                        <span className="px-2.5 py-1 rounded-full bg-[#C74735] text-[10px] font-extrabold uppercase text-white shadow-sm">
                          {sample.sourceLanguage.toUpperCase()}
                        </span>
                      </div>

                      {/* Bottom Image Label */}
                      <div className="absolute bottom-2.5 left-3 right-3 flex items-center justify-between text-white">
                        <span className="text-xs font-bold drop-shadow-sm">
                          {t("demos.dishesCount", { count: sample.dishCount })}
                        </span>
                        <span className="text-[11px] bg-black/40 backdrop-blur-xs px-2 py-0.5 rounded-md text-[#F2DFD3]">
                          {t("demos.offlineReady")}
                        </span>
                      </div>
                    </div>

                    {/* Card Body */}
                    <div className="p-4 flex flex-col gap-2 flex-1 justify-between">
                      <div className="flex flex-col gap-1">
                        <h4 className="text-base font-bold text-[#1F1B18] group-hover:text-[#C74735] transition-colors leading-snug">
                          {sample.name}
                        </h4>
                        <p className="text-xs text-[#70645C] line-clamp-2 leading-relaxed">
                          {sample.description}
                        </p>
                      </div>

                      <div className="pt-3 border-t border-[#EADFD5] flex items-center justify-between">
                        <span className="text-xs font-bold text-[#C74735] flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                          {t("demos.exploreMenu")} <ArrowRight className="w-3.5 h-3.5" />
                        </span>
                        <span className="text-[11px] text-[#70645C] font-mono">
                          {t("demos.instantDemo")}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Photo Orientation & Rotation Preview if file selected and not currently processing */}
            {pendingFile && !isProcessing && (
              <div className="p-6 rounded-3xl bg-[#FFFFFF] border border-[#EADFD5] shadow-xl flex flex-col items-center gap-4 animate-in fade-in">
                <div className="flex items-center justify-between w-full">
                  <span className="text-xs font-bold text-[#1F1B18] flex items-center gap-2">
                    <RotateCw className="w-4 h-4 text-[#C74735]" />
                    {t("preview.adjustTitle")}
                  </span>
                  <button
                    type="button"
                    onClick={() => setRotation((r) => (r + 90) % 360)}
                    className="px-3.5 py-1.5 rounded-xl bg-[#FBF2ED] hover:bg-[#F2DFD3] text-[#1F1B18] text-xs font-bold border border-[#EADFD5] flex items-center gap-1.5 transition-all cursor-pointer"
                  >
                    <RotateCw className="w-3.5 h-3.5 text-[#C74735]" />
                    <span>{t("preview.rotate90", { rotation })}</span>
                  </button>
                </div>

                <div className="w-56 h-56 rounded-2xl overflow-hidden bg-[#1F1B18] border border-[#EADFD5] flex items-center justify-center p-2 shadow-inner">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={pendingPreviewUrl || ""}
                    alt="Menu preview"
                    className="max-h-full max-w-full object-contain transition-transform duration-300"
                    style={{ transform: `rotate(${rotation}deg)` }}
                  />
                </div>

                <div className="flex items-center gap-3 w-full">
                  <button
                    type="button"
                    onClick={() => {
                      setPendingFile(null);
                      setPendingPreviewUrl(null);
                      setRotation(0);
                    }}
                    className="px-4 py-2.5 rounded-xl bg-[#FBF2ED] hover:bg-[#F2DFD3] text-[#70645C] text-xs font-semibold cursor-pointer border border-[#EADFD5] transition-colors"
                  >
                    {t("preview.cancel")}
                  </button>
                  <button
                    type="button"
                    disabled={isProcessing}
                    onClick={() => handleAnalyzeMenuImage(pendingFile, rotation)}
                    className="flex-1 py-2.5 rounded-xl bg-[#C74735] hover:bg-[#A52F20] text-white font-bold text-xs shadow-lg shadow-[#C74735]/25 transition-all cursor-pointer flex items-center justify-center gap-2"
                  >
                    <Sparkles className="w-4 h-4 text-white" />
                    <span>{t("preview.extractButton", { rotation })}</span>
                  </button>
                </div>
              </div>
            )}

            {/* Drag & Drop Upload Zone */}
            <label
              htmlFor="menu-photo-upload"
              onDragOver={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsDragging(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsDragging(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setIsDragging(false);
                if (isProcessing) return;
                const file = e.dataTransfer.files?.[0];
                if (file) handleFileSelect(file);
              }}
              className={`relative w-full rounded-2xl p-8 flex flex-col items-center justify-center text-center gap-3 transition-all cursor-pointer shadow-sm group select-none ${
                isDragging
                  ? "bg-[#F5ECE7] border-2 border-[#C74735] scale-[1.01]"
                  : "bg-[#FBF2ED] hover:bg-[#F5ECE7] border-2 border-dashed border-[#EADFD5] hover:border-[#C74735]/50"
              }`}
            >
              <div className={`w-14 h-14 rounded-full flex items-center justify-center text-[#C74735] group-hover:scale-110 transition-transform shadow-xs pointer-events-none ${
                isDragging ? "bg-[#C74735] text-white" : "bg-[#F2DFD3]"
              }`}>
                <Upload className="w-7 h-7" />
              </div>
              <div className="flex flex-col pointer-events-none">
                <span className="text-sm font-bold text-[#1F1B18]">
                  {isDragging ? t("dropzone.activeTitle") : t("dropzone.idleTitle")}
                </span>
                <span className="text-xs text-[#70645C] mt-1">
                  {t("dropzone.sub")}
                </span>
              </div>
            </label>

            {/* User Dietary Restrictions Selector */}
            <div className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm">
              <DietaryPreferencesSelector
                selected={userRestrictions}
                onChange={setUserRestrictions}
              />
            </div>

            {/* How It Works (3-Step Visual Cards) */}
            <div className="flex flex-col gap-4">
              <div className="flex flex-col">
                <span className="text-xs font-bold uppercase tracking-wider text-[#C74735]">
                  {t("steps.tag")}
                </span>
                <h3 className="text-lg font-bold text-[#1F1B18]">
                  {t("steps.title")}
                </h3>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-[#FFFFFF] p-5 rounded-2xl border border-[#EADFD5] flex flex-col gap-2.5 shadow-sm">
                  <div className="w-8 h-8 rounded-full bg-[#F2DFD3] text-[#C74735] font-bold text-xs flex items-center justify-center">
                    1
                  </div>
                  <h4 className="text-xs font-bold text-[#1F1B18]">
                    {t("steps.step1Title")}
                  </h4>
                  <p className="text-xs text-[#70645C] leading-relaxed">
                    {t("steps.step1Desc")}
                  </p>
                </div>

                <div className="bg-[#FFFFFF] p-5 rounded-2xl border border-[#EADFD5] flex flex-col gap-2.5 shadow-sm">
                  <div className="w-8 h-8 rounded-full bg-[#F2DFD3] text-[#C74735] font-bold text-xs flex items-center justify-center">
                    2
                  </div>
                  <h4 className="text-xs font-bold text-[#1F1B18]">
                    {t("steps.step2Title")}
                  </h4>
                  <p className="text-xs text-[#70645C] leading-relaxed">
                    {t("steps.step2Desc")}
                  </p>
                </div>

                <div className="bg-[#FFFFFF] p-5 rounded-2xl border border-[#EADFD5] flex flex-col gap-2.5 shadow-sm">
                  <div className="w-8 h-8 rounded-full bg-[#F2DFD3] text-[#C74735] font-bold text-xs flex items-center justify-center">
                    3
                  </div>
                  <h4 className="text-xs font-bold text-[#1F1B18]">
                    {t("steps.step3Title")}
                  </h4>
                  <p className="text-xs text-[#70645C] leading-relaxed">
                    {t("steps.step3Desc")}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* SCREEN 2: PRIMARY TRANSLATED MENU & INTERACTIVE OVERLAY */}
        {activeScreen === "results" && currentImageUrl && analysisResult && (
          <div className="flex flex-col gap-5 animate-in fade-in">
            {/* Restaurant Meta & Language Banner */}
            <div className="w-full bg-[#FBF2ED] rounded-3xl p-5 border border-[#EADFD5] shadow-sm flex flex-col gap-4">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-2.5 min-w-0">
                  <div className="p-2 rounded-xl bg-[#FFF8F5] text-[#C74735] border border-[#EADFD5] shadow-sm">
                    <Store className="w-5 h-5 text-[#C74735]" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-[#1F1B18] truncate">
                      {analysisResult.menu_metadata.restaurant_id || t("results.analyzedBadge")}
                    </h2>
                    <p className="text-xs text-[#70645C]">
                      {t("results.dishesCount", { count: analysisResult.dishes.length })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#EAF5EE] text-[#166742] border border-[#B2DEC4] text-xs font-bold shadow-sm">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#166742]" />
                    {t("results.verifiedOcr") || "Verified OCR"}
                  </span>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#FFF8F5] hover:bg-[#F2DFD3] text-[#1F1B18] text-xs font-bold border border-[#EADFD5] transition-all cursor-pointer shadow-sm active:scale-95"
                  >
                    <ArrowLeft className="w-3.5 h-3.5 text-[#C74735]" />
                    <span>{t("results.scanAnother") || "Scan Another"}</span>
                  </button>
                </div>
              </div>

              {/* Quick Language Selector & View Switcher */}
              <div className="flex items-center justify-between flex-wrap gap-3 pt-1 border-t border-[#EADFD5]/60">
                {/* Language Pair Pill */}
                <div className="flex items-center gap-2 flex-wrap">
                  <div className="flex items-center gap-2 bg-[#FFF8F5] px-3.5 py-1.5 rounded-full border border-[#EADFD5] shadow-sm text-xs">
                    <span className="font-semibold text-[#1F1B18] flex items-center gap-1">
                      <Globe className="w-3.5 h-3.5 text-[#C74735]" />
                      {analysisResult.menu_metadata.source_language
                        ? analysisResult.menu_metadata.source_language.toUpperCase()
                        : "ORIGINAL"}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#70645C]" />
                    <span className="font-bold text-[#C74735]">
                      {targetLanguage.toUpperCase()}
                    </span>
                  </div>

                  <LanguageSelector
                    value={targetLanguage}
                    disabled={isRetranslating}
                    onChange={(lang) => {
                      setTargetLanguage(lang);
                      handleRetranslate(lang);
                    }}
                  />

                  <button
                    type="button"
                    disabled={isRetranslating}
                    onClick={() => handleRetranslate(targetLanguage)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#C74735] hover:bg-[#A52F20] text-white text-xs font-bold transition-all cursor-pointer shadow-sm shadow-[#C74735]/20 disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isRetranslating ? "animate-spin" : ""}`} />
                    <span>
                      {isRetranslating
                        ? t("results.retranslating", { language: targetLanguage.toUpperCase() })
                        : t("results.retranslate") || "Retranslate"}
                    </span>
                  </button>
                </div>

                {/* View Switcher Toggle */}
                <div className="flex items-center rounded-full bg-[#F2DFD3] p-1 border border-[#EADFD5] shrink-0">
                  <button
                    type="button"
                    onClick={() => setResultsTab("menu")}
                    className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                      resultsTab === "menu"
                        ? "bg-[#C74735] text-white shadow-md shadow-[#C74735]/25"
                        : "text-[#70645C] hover:text-[#1F1B18]"
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>{t("results.tabStructured")}</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setResultsTab("overlay")}
                    className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer ${
                      resultsTab === "overlay"
                        ? "bg-[#C74735] text-white shadow-md shadow-[#C74735]/25"
                        : "text-[#70645C] hover:text-[#1F1B18]"
                    }`}
                  >
                    <ImageIcon className="w-3.5 h-3.5" />
                    <span>{t("results.tabOverlay")}</span>
                  </button>
                </div>
              </div>

              {/* Search input in banner */}
              <div className="relative w-full">
                <Search className="w-4 h-4 text-[#70645C] absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder={t("results.searchPlaceholder")}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#FFFFFF] border border-[#EADFD5] text-xs text-[#1F1B18] placeholder-[#70645C] focus:outline-none focus:border-[#C74735] shadow-sm transition-all"
                />
              </div>
            </div>

            {/* Empty State Banner if 0 dishes detected */}
            {analysisResult.dishes.length === 0 && (
              <div className="p-5 rounded-2xl bg-[#FCF5EB] border border-[#F0D6AF] text-[#9B6416] text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm">
                <div className="flex items-center gap-2.5">
                  <AlertCircle className="w-5 h-5 text-[#9B6416] shrink-0" />
                  <span className="font-medium leading-relaxed">
                    {t("results.noLegibleDishes") || "No legible dishes could be extracted from this photo. If your menu was photographed sideways, try rotating it 90° before scanning, or explore our pre-loaded demo menus."}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={handleReset}
                  className="px-4 py-2 rounded-xl bg-[#F2DFD3] hover:bg-[#EADFD5] text-[#1F1B18] font-bold shrink-0 cursor-pointer transition-colors border border-[#EADFD5]"
                >
                  {t("results.tryAnotherPhoto") || "Try Another Photo"}
                </button>
              </div>
            )}

            {/* Performance & Stage Latency Collapsible Banner */}
            {analysisResult.processing_metadata && (
              <div className="rounded-2xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm overflow-hidden transition-all">
                <button
                  type="button"
                  onClick={() => setShowPerformanceMetrics(!showPerformanceMetrics)}
                  className="w-full px-4 py-2.5 flex items-center justify-between text-xs text-[#70645C] hover:text-[#1F1B18] transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1.5 font-bold text-[#C74735]">
                      <Activity className="w-3.5 h-3.5 text-[#C74735]" />
                      Latency: {(analysisResult.processing_metadata.total_latency_ms / 1000).toFixed(1)}s
                    </span>
                    <span className="text-[#EADFD5] hidden sm:inline">•</span>
                    <span className="text-[#70645C] hidden sm:inline">
                      Model: <span className="font-mono text-[#1F1B18] font-semibold">{analysisResult.processing_metadata.model_name}</span>
                    </span>
                    {analysisResult.processing_metadata.diagnostics?.tokens_per_second != null && (
                      <>
                        <span className="text-[#EADFD5] hidden sm:inline">•</span>
                        <span className="text-[#166742] hidden sm:flex items-center gap-1 font-mono font-semibold">
                          <Zap className="w-3 h-3 text-[#166742]" />
                          {Number(analysisResult.processing_metadata.diagnostics.tokens_per_second).toFixed(1)} tok/s
                        </span>
                      </>
                    )}
                  </div>
                  <div className="flex items-center gap-1 text-[11px] font-semibold text-[#70645C]">
                    <span>{showPerformanceMetrics ? "Hide Telemetry" : "View 8 Pipeline Stages"}</span>
                    {showPerformanceMetrics ? (
                      <ChevronUp className="w-3.5 h-3.5 text-[#70645C]" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-[#70645C]" />
                    )}
                  </div>
                </button>

                {showPerformanceMetrics && (
                  <div className="p-4 pt-1 border-t border-[#EADFD5] bg-[#FBF2ED]">
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2.5 mb-3">
                      <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm">
                        <div className="text-[10px] uppercase font-bold text-[#70645C]">Total Latency</div>
                        <div className="text-sm font-bold text-[#1F1B18] mt-0.5">
                          {(analysisResult.processing_metadata.total_latency_ms / 1000).toFixed(2)}s
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm">
                        <div className="text-[10px] uppercase font-bold text-[#70645C]">Residency</div>
                        <div className="text-sm font-bold text-[#C74735] mt-0.5 capitalize">
                          {String(analysisResult.processing_metadata.diagnostics?.model_residency || "VRAM Resident").replace(/_/g, " ")}
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm">
                        <div className="text-[10px] uppercase font-bold text-[#70645C]">Tokens & Speed</div>
                        <div className="text-sm font-bold text-[#166742] mt-0.5">
                          {Number(analysisResult.processing_metadata.diagnostics?.eval_tokens || 0)} tok @ {Number(analysisResult.processing_metadata.diagnostics?.tokens_per_second || 0).toFixed(1)} tok/s
                        </div>
                      </div>
                      <div className="p-3 rounded-xl bg-[#FFFFFF] border border-[#EADFD5] shadow-sm">
                        <div className="text-[10px] uppercase font-bold text-[#70645C]">RAG Knowledge</div>
                        <div className="text-sm font-bold text-[#1F1B18] mt-0.5 capitalize">
                          {analysisResult.processing_metadata.retrieval_status.replace(/_/g, " ")}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <div className="text-[11px] font-bold text-[#70645C] uppercase tracking-wider mb-1">
                        Measured Stage Telemetry (Request: {analysisResult.processing_metadata.request_id})
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                        {analysisResult.processing_metadata.stages.map((stage, idx) => (
                          <div
                            key={idx}
                            className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-[#FFFFFF] border border-[#EADFD5]"
                          >
                            <span className="font-mono text-[#70645C] capitalize">
                              {stage.stage.replace(/_/g, " ")}
                            </span>
                            <span className="font-mono font-bold text-[#1F1B18]">
                              {stage.duration_ms >= 1000
                                ? `${(stage.duration_ms / 1000).toFixed(2)}s`
                                : `${stage.duration_ms.toFixed(1)}ms`}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 1: PRIMARY TRANSLATED MENU VIEW */}
            {resultsTab === "menu" && analysisResult.dishes.length > 0 && (() => {
              // Extract unique category sections
              const sections = Array.from(
                new Set(
                  analysisResult.dishes
                    .map((d) => d.section?.trim())
                    .filter((s): s is string => Boolean(s))
                )
              );

              // Filter dishes according to search query and selected section
              const filteredDishes = analysisResult.dishes.filter((dish) => {
                if (selectedSection !== "all" && dish.section?.trim() !== selectedSection) {
                  return false;
                }
                if (searchQuery.trim()) {
                  const q = searchQuery.toLowerCase().trim();
                  const matchesTitle = dish.translated_title.toLowerCase().includes(q);
                  const matchesOriginal = dish.original_text.toLowerCase().includes(q);
                  const matchesPhonetic = (dish.phonetic_transcription || "").toLowerCase().includes(q);
                  const matchesDesc = (dish.culinary_description || "").toLowerCase().includes(q);
                  return matchesTitle || matchesOriginal || matchesPhonetic || matchesDesc;
                }
                return true;
              });

              // Group by section
              const grouped: Record<string, AnalyzedDish[]> = {};
              for (const dish of filteredDishes) {
                const sec = dish.section?.trim() || "Menu Items";
                if (!grouped[sec]) grouped[sec] = [];
                grouped[sec].push(dish);
              }

              const isRtl = targetLanguage === "ar";

              return (
                <div dir={isRtl ? "rtl" : "ltr"} className="flex flex-col gap-6">
                  {/* Category Nav Carousel (Horizontal Scroll) */}
                  {sections.length > 0 && (
                    <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
                      <button
                        type="button"
                        onClick={() => setSelectedSection("all")}
                        className={`px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap cursor-pointer transition-all shadow-sm ${
                          selectedSection === "all"
                            ? "bg-[#C74735] text-white shadow-md shadow-[#C74735]/25"
                            : "bg-[#FFFFFF] text-[#70645C] border border-[#EADFD5] hover:text-[#1F1B18]"
                        }`}
                      >
                        {t("results.allSections")} ({analysisResult.dishes.length})
                      </button>
                      {sections.map((sec) => {
                        const count = analysisResult.dishes.filter((d) => d.section?.trim() === sec).length;
                        return (
                          <button
                            key={sec}
                            type="button"
                            onClick={() => setSelectedSection(sec)}
                            className={`px-4 py-1.5 rounded-full text-xs font-bold whitespace-nowrap cursor-pointer transition-all shadow-sm ${
                              selectedSection === sec
                                ? "bg-[#C74735] text-white shadow-md shadow-[#C74735]/25"
                                : "bg-[#FFFFFF] text-[#70645C] border border-[#EADFD5] hover:text-[#1F1B18]"
                            }`}
                          >
                            {sec} ({count})
                          </button>
                        );
                      })}
                    </div>
                  )}

                  {/* Dietary Quick Toggle Chips */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[11px] text-[#70645C] font-bold uppercase tracking-wider mr-1">
                      {t("results.filters") || "Filters:"}
                    </span>
                    {["gluten", "dairy", "vegan", "shellfish"].map((tag) => {
                      const active = userRestrictions.includes(tag);
                      return (
                        <button
                          key={tag}
                          type="button"
                          onClick={() => {
                            if (active) {
                              setUserRestrictions(userRestrictions.filter((r) => r !== tag));
                            } else {
                              setUserRestrictions([...userRestrictions, tag]);
                            }
                          }}
                          className={`px-3 py-1 rounded-full text-xs font-bold cursor-pointer transition-all shadow-sm ${
                            active
                              ? "bg-[#F2DFD3] text-[#A52F20] border border-[#C74735]/40"
                              : "bg-[#FFFFFF] text-[#70645C] border border-[#EADFD5] hover:text-[#1F1B18]"
                          }`}
                        >
                          {active ? `✓ ${tag}` : tag}
                        </button>
                      );
                    })}
                  </div>

                  {/* Grouped Section Cards */}
                  {Object.entries(grouped).map(([sectionTitle, sectionDishes]) => (
                    <div key={sectionTitle} className="flex flex-col gap-3">
                      <div className="flex items-center gap-2 px-1">
                        <UtensilsCrossed className="w-4 h-4 text-[#C74735]" />
                        <h3 className="text-sm font-extrabold uppercase tracking-wider text-[#1F1B18]">
                          {sectionTitle}
                        </h3>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#F2DFD3] text-[#6F6258]">
                          {sectionDishes.length}
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {sectionDishes.map((dish) => {
                          const isSelected = selectedDish?.dish_id === dish.dish_id;
                          const hasConflict =
                            dish.dietary_compatibility?.user_conflicts &&
                            dish.dietary_compatibility.user_conflicts.length > 0;

                          return (
                            <div
                              key={dish.dish_id}
                              onClick={() => setSelectedDish(dish)}
                              className={`p-5 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between gap-3 ${
                                isRtl ? "text-right" : "text-left"
                              } relative overflow-hidden group shadow-sm hover:shadow-md ${
                                isSelected
                                  ? "bg-[#FFFFFF] border-[#C74735] ring-2 ring-[#C74735] shadow-lg shadow-[#C74735]/10"
                                  : "bg-[#FFFFFF] hover:bg-[#FBF2ED]/50 border-[#EADFD5]"
                              }`}
                            >
                              {/* Stitch Red Left Indicator Bar */}
                              <div
                                className={`w-1.5 absolute left-0 top-0 bottom-0 ${
                                  isSelected ? "bg-[#C74735]" : "bg-[#C74735]/40 group-hover:bg-[#C74735]"
                                } transition-colors`}
                              />

                              <div className="flex flex-col gap-2.5 pl-2">
                                {/* Representative Food Photograph */}
                                <DishImage
                                  imageInfo={dish.representative_image}
                                  dishName={dish.translated_name || dish.translated_title || dish.original_name || dish.original_text}
                                  aspectRatioClass="aspect-[16/10]"
                                  onRetry={() => handleRetryDishImage(dish.dish_id)}
                                />

                                {/* Title, Tags, and Price */}
                                <div className="flex items-start justify-between gap-3 pt-0.5">
                                  <div className="flex flex-col gap-0.5">
                                    <div className="flex items-center gap-2 flex-wrap">
                                      <h4 className="text-base font-bold text-[#1F1B18] group-hover:text-[#C74735] transition-colors leading-snug">
                                        {dish.translated_name ||
                                          dish.translated_title ||
                                          dish.original_name ||
                                          dish.original_text}
                                      </h4>
                                      {dish.tags?.map((tag, tIdx) => (
                                        <span
                                          key={tIdx}
                                          className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider bg-[#FCF5EB] text-[#9B6416] border border-[#F0D6AF]"
                                        >
                                          ⭐ {tag}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                  {(dish.price_text_original || dish.price) && (
                                    <span className="px-2.5 py-1 rounded-xl text-xs font-extrabold bg-[#FBF2ED] border border-[#EADFD5] text-[#A52F20] shrink-0 font-mono shadow-sm">
                                      {dish.price_currency || dish.currency ? `${dish.price_currency || dish.currency} ` : ""}{dish.price_text_original || dish.price}
                                    </span>
                                  )}
                                </div>

                                {/* Original Native Text and Phonetic Transcription (Explicit verification box) */}
                                <div className="flex items-center gap-2 flex-wrap bg-[#F5ECE7] px-2.5 py-1.5 rounded-xl border border-[#EADFD5] text-xs">
                                  <span className="text-[10px] uppercase font-bold text-[#70645C] tracking-wider">
                                    {t("results.original") || "Original:"}
                                  </span>
                                  <span className="text-[#1F1B18] font-bold">
                                    {dish.original_name || dish.original_text}
                                  </span>
                                  {(dish.transliteration || dish.phonetic_transcription) && (
                                    <span className="text-xs text-[#A52F20] italic font-mono flex items-center gap-1 border-l border-[#EADFD5] pl-2 ml-1">
                                      <span>🗣️</span> {dish.transliteration || dish.phonetic_transcription}
                                    </span>
                                  )}
                                </div>

                                {/* Culinary Description */}
                                {dish.translated_description || dish.culinary_description ? (
                                  <p className="text-xs text-[#58413D] leading-relaxed mt-0.5 line-clamp-2">
                                    {dish.translated_description || dish.culinary_description}
                                  </p>
                                ) : (
                                  <p className="text-[11px] text-[#70645C] italic mt-0.5">
                                    {t("results.noDescription") || "No description provided on the menu"}
                                  </p>
                                )}

                                {/* AI-Generated Explanation (clearly segregated) */}
                                {dish.generated_description && (
                                  <div className="mt-1 p-2.5 rounded-xl bg-[#FBF2ED] border border-[#EADFD5] text-[11px] text-[#58413D] leading-relaxed">
                                    <span className="font-bold text-[#C74735] block text-[10px] uppercase tracking-wider mb-0.5">
                                      {t("results.aiExplanation") || "AI Dish Explanation:"}
                                    </span>
                                    {dish.generated_description}
                                  </div>
                                )}

                                {/* Flavor Profile Pill Tags */}
                                {dish.flavor_profile && (
                                  <div className="flex items-center gap-1.5 flex-wrap pt-1">
                                    {dish.flavor_profile.split(",").map((flavor, i) => (
                                      <span
                                        key={i}
                                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#FFF8F5] text-[#70645C] border border-[#EADFD5]"
                                      >
                                        ✨ {flavor.trim()}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>

                              {/* Safety & Allergen Badges */}
                              <div className="pt-2 pl-2 border-t border-[#EADFD5] flex flex-wrap items-center justify-between gap-2">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                  {hasConflict && (
                                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#FFDAD6] text-[#BA1A1A] border border-[#FFDAD6] text-[10px] font-bold">
                                      <ShieldAlert className="w-3 h-3 text-[#BA1A1A]" />
                                      {dish.dietary_compatibility.user_conflicts.join(", ")} {t("results.conflict") || "Conflict"}
                                    </span>
                                  )}

                                  {dish.allergen_warnings.slice(0, 2).map((aw, i) => (
                                    <span
                                      key={i}
                                      className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-[#FCF5EB] border border-[#F0D6AF] text-[#9B6416]"
                                    >
                                      ⚠️ {aw.allergen}
                                    </span>
                                  ))}

                                  {dish.dietary_compatibility.vegan === "yes" && (
                                    <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-[#EAF5EE] border border-[#B2DEC4] text-[#166742]">
                                      🌱 Vegan
                                    </span>
                                  )}
                                </div>

                                <div className="text-[11px] font-bold text-[#C74735] group-hover:translate-x-1 transition-transform flex items-center gap-1">
                                  <span>{t("results.details")}</span>
                                  <ChevronRight className="w-3.5 h-3.5" />
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })()}

            {/* TAB 2: INTERACTIVE PHOTO OVERLAY */}
            {resultsTab === "overlay" && (
              <MenuCanvasOverlay
                imageUrl={currentImageUrl}
                dishes={analysisResult.dishes}
                selectedDish={selectedDish}
                onSelectDish={setSelectedDish}
                userRestrictions={userRestrictions}
              />
            )}

            {/* Bottom Sheet / Side Drawer for Selected Dish Details */}
            <DishDetailDrawer
              dish={selectedDish}
              onClose={() => setSelectedDish(null)}
              onNextDish={handleNextDish}
              onPrevDish={handlePrevDish}
              hasNext={currentDishIndex < dishes.length - 1}
              hasPrev={currentDishIndex > 0}
            />
          </div>
        )}
      </main>

      {/* Camera Capture Modal */}
      <CameraCaptureModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={(file) => {
          setIsCameraOpen(false);
          handleAnalyzeMenuImage(file, rotation);
        }}
      />

      {/* Processing State Modal */}
      {isProcessing && (
        <ProcessingOverlay
          imageUrl={currentImageUrl || pendingPreviewUrl}
          onCancel={handleCancelProcessing}
        />
      )}
    </div>
  );
}

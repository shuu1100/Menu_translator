"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Camera,
  Upload,
  RefreshCw,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  UtensilsCrossed,
  ArrowRight,
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
import { OfflineBanner } from "../components/OfflineBanner";
import { SAMPLE_MENUS } from "../data/sample_menus";
import { apiClient } from "../services/apiClient";

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

const PHASES = [
  { id: 1, name: "Workspace Audit & Skeleton", status: "completed" },
  { id: 2, name: "VLM Inference & Extraction", status: "completed" },
  { id: 3, name: "Backend Contracts & Pipeline", status: "completed" },
  { id: 4, name: "SQLite & Hybrid RAG", status: "completed" },
  { id: 5, name: "Translation & Allergen Safety", status: "completed" },
  { id: 6, name: "Dataset Creation & Fine-Tuning", status: "completed" },
  { id: 7, name: "PWA Camera & BBox Overlays", status: "completed" },
  { id: 8, name: "Integration & Offline Mode", status: "completed" },
  { id: 9, name: "QA, Demo & Hacktoberfest Release", status: "upcoming" },
];

export default function Home() {
  // Navigation & Screen state
  const [activeScreen, setActiveScreen] = useState<"capture" | "results">("capture");
  const [targetLanguage, setTargetLanguage] = useState<SupportedLanguage>("en");
  const [userRestrictions, setUserRestrictions] = useState<string[]>(["gluten", "dairy"]);

  // Camera & Upload state
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Analysis result state
  const [currentImageUrl, setCurrentImageUrl] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<MenuAnalysisResponse | null>(null);
  const [selectedDish, setSelectedDish] = useState<AnalyzedDish | null>(null);

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

  // Analyze uploaded or captured image via backend API
  const handleAnalyzeMenuImage = async (file: File) => {
    setIsProcessing(true);
    setErrorMessage(null);

    const objectUrl = URL.createObjectURL(file);
    setCurrentImageUrl(objectUrl);

    try {
      const result = await apiClient.analyzeMenu({
        file,
        targetLanguage,
        dietaryRestrictions: userRestrictions,
      });

      setAnalysisResult(result);
      setSelectedDish(result.dishes[0] || null);
      setActiveScreen("results");
    } catch (err: unknown) {
      const msg =
        (err as { message?: string })?.message ||
        (err instanceof Error ? err.message : "Failed to analyze menu.");
      setErrorMessage(
        `${msg} (Tip: You can also explore pre-loaded demo menus below without live inference).`
      );
    } finally {
      setIsProcessing(false);
    }
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
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Offline / Service Status Banner */}
      <OfflineBanner
        backendReachable={health !== null}
        modelReady={health?.services.model_service?.status === "healthy" || health?.services.model_service?.status === "ok"}
        onRefresh={fetchHealth}
      />

      {/* Main Top Navigation Header */}
      <header className="sticky top-0 z-30 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
            <Camera className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
              Menu Translator
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                PWA Active
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Privacy-Preserving Local AI Culinary Lens
            </p>
          </div>
        </div>

        {/* Global Controls */}
        <div className="flex items-center gap-2.5">
          <LanguageSelector
            value={targetLanguage}
            onChange={setTargetLanguage}
          />

          {activeScreen === "results" && (
            <button
              type="button"
              onClick={handleReset}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-semibold text-slate-200 transition-colors cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Menu</span>
            </button>
          )}
        </div>
      </header>

      {/* App Body */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
        {/* Error Alert if encountered */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-500/15 border border-rose-500/30 text-rose-200 text-xs flex items-start justify-between gap-3 animate-in fade-in">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">{errorMessage}</p>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-white font-bold"
            >
              ×
            </button>
          </div>
        )}

        {/* SCREEN 1: LANDING & CAPTURE */}
        {activeScreen === "capture" && (
          <div className="flex flex-col gap-8 max-w-2xl mx-auto w-full py-4">
            {/* Hero Card */}
            <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-indigo-950/40 via-slate-900/60 to-slate-950 border border-indigo-500/20 shadow-2xl flex flex-col gap-5 text-center sm:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium w-fit mx-auto sm:mx-0">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Zero Cloud Dependencies • 100% Private</span>
              </div>
              <div>
                <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
                  Point, Scan, & Safely Understand Any Restaurant Menu
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 mt-2 leading-relaxed">
                  Real-time visual extraction powered by local Qwen3-VL and an isolated culinary knowledge base. Tap any dish on your screen for authentic explanations, cultural flavor profiles, and evidence-grounded allergen checks.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsCameraOpen(true)}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-xl shadow-indigo-600/25 transition-all cursor-pointer active:scale-98"
                >
                  <Camera className="w-4 h-4" />
                  <span>Scan with Camera</span>
                </button>

                <label className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-slate-200 text-sm font-medium transition-all cursor-pointer">
                  <Upload className="w-4 h-4 text-slate-400" />
                  <span>Upload Menu Photo</span>
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) handleAnalyzeMenuImage(file);
                    }}
                  />
                </label>
              </div>
            </div>

            {/* User Dietary Restrictions Selector */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 backdrop-blur-sm">
              <DietaryPreferencesSelector
                selected={userRestrictions}
                onChange={setUserRestrictions}
              />
            </div>

            {/* Instant Demo Menus */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <UtensilsCrossed className="w-3.5 h-3.5 text-indigo-400" />
                  Try Pre-loaded Demo Menus
                </h3>
                <span className="text-[11px] text-slate-400">Offline Ready</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {SAMPLE_MENUS.map((menu) => (
                  <button
                    key={menu.id}
                    type="button"
                    onClick={() => handleLoadSampleMenu(menu.id)}
                    className="p-4 rounded-2xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-indigo-500/50 text-left transition-all group flex flex-col justify-between gap-3 shadow-md hover:shadow-indigo-500/5 cursor-pointer"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                          {menu.name}
                        </span>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                          {menu.cuisine}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                        {menu.description}
                      </p>
                    </div>

                    <div className="flex items-center gap-1 text-xs font-semibold text-indigo-400 group-hover:translate-x-1 transition-transform">
                      <span>Explore Interactive Overlay</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Roadmap Status */}
            <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/60 flex flex-col gap-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Development Roadmap
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                {PHASES.map((p) => (
                  <div
                    key={p.id}
                    className={`p-2 rounded-lg border text-[11px] flex items-center justify-between ${
                      p.status === "completed"
                        ? "bg-indigo-950/20 border-indigo-500/30 text-indigo-200"
                        : "bg-slate-950 border-slate-800/80 text-slate-500"
                    }`}
                  >
                    <span className="truncate">Phase {p.id}: {p.name}</span>
                    {p.status === "completed" && (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* SCREEN 2: INTERACTIVE MENU OVERLAY & DETAILS */}
        {activeScreen === "results" && currentImageUrl && analysisResult && (
          <div className="flex flex-col gap-4">
            {/* Results Filter & Status Toolbar */}
            <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-md flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  {analysisResult.dishes.length} Dishes Found
                </span>
                <span className="text-xs text-slate-400 hidden sm:inline">
                  Tap any box to inspect ingredients, pronunciation, and allergens.
                </span>
              </div>

              {/* Quick Restriction Filter Chips */}
              <div className="flex items-center gap-1.5 flex-wrap">
                <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider mr-1">
                  Filters:
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
                      className={`px-2.5 py-1 rounded-full text-xs font-medium cursor-pointer transition-all ${
                        active
                          ? "bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm shadow-amber-500/10"
                          : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-slate-200"
                      }`}
                    >
                      {active ? `✓ ${tag}` : tag}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Interactive Canvas Overlay */}
            <MenuCanvasOverlay
              imageUrl={currentImageUrl}
              dishes={analysisResult.dishes}
              selectedDish={selectedDish}
              onSelectDish={setSelectedDish}
              userRestrictions={userRestrictions}
            />

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
        onCapture={handleAnalyzeMenuImage}
      />

      {/* Processing State Modal */}
      {isProcessing && (
        <ProcessingOverlay onCancel={() => setIsProcessing(false)} />
      )}
    </div>
  );
}

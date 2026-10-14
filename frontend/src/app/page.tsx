"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Camera,
  CheckCircle2,
  Cpu,
  Database,
  Globe2,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

interface ServiceInfo {
  status: "ok" | "degraded" | "unavailable";
  message: string;
  details?: Record<string, unknown>;
}

interface HealthData {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  timestamp: string;
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
  { id: 5, name: "Translation & Allergen Safety", status: "upcoming" },
  { id: 6, name: "Dataset Creation & Fine-Tuning", status: "upcoming" },
  { id: 7, name: "PWA Camera & BBox Overlays", status: "upcoming" },
  { id: 8, name: "Integration & Offline Mode", status: "upcoming" },
  { id: 9, name: "QA, Demo & Hacktoberfest Release", status: "upcoming" },
];

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
      if (!res.ok) {
        throw new Error(`Health check returned HTTP ${res.status}`);
      }
      const data: HealthData = await res.json();
      setHealth(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to connect to backend";
      setError(msg);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "ok":
      case "healthy":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" /> Healthy
          </span>
        );
      case "degraded":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" /> Degraded
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3.5 h-3.5" /> Offline
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      {/* Background glow effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-gradient-to-b from-indigo-500/15 via-purple-500/10 to-transparent blur-3xl opacity-70" />
      </div>

      <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col gap-10">
        {/* Navigation header */}
        <header className="flex items-center justify-between border-b border-slate-800/80 pb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Camera className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Menu Translator
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Phase 3 Ready
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Privacy-Preserving Local AI Culinary Lens
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchHealth}
              disabled={loading}
              className="inline-flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700/60 text-slate-200 transition-colors shadow-sm disabled:opacity-50"
              title="Refresh status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
              Re-check Health
            </button>
          </div>
        </header>

        {/* Hero Section */}
        <section className="text-center sm:text-left max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 mb-4">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Hacktoberfest Open-Source AI Challenge
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Local Vision-Language Menu Translation & Allergen Safety
          </h2>
          <p className="mt-3 text-base text-slate-400 leading-relaxed">
            A self-hosted edge application built with Next.js PWA, FastAPI, and local VLM models (Qwen3-VL/Qwen2.5-VL via Ollama) with SQLite hybrid RAG for culinary translation and dietary allergen protection.
          </p>
        </section>

        {/* Live Service Diagnostics */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Activity className="w-4 h-4 text-indigo-400" />
              Real-time Subsystem Status
            </h3>
            {health && getStatusBadge(health.status)}
          </div>

          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-200 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="flex flex-col gap-1">
                <span className="font-semibold">Backend Unreachable</span>
                <span className="text-xs text-rose-300/90">
                  {error}. Make sure the FastAPI backend is running via{" "}
                  <code className="bg-rose-900/40 px-1 py-0.5 rounded font-mono">
                    uvicorn backend.app.main:app --port 8000
                  </code>
                </span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* API Card */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Globe2 className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">FastAPI Backend</h4>
                    <p className="text-xs text-slate-400">REST & Schema Orchestrator</p>
                  </div>
                </div>
                {getStatusBadge(health?.services.api?.status)}
              </div>
              <div className="text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                {health?.services.api ? (
                  <span>Version: {health.version} ({health.environment})</span>
                ) : (
                  <span>Checking connection...</span>
                )}
              </div>
            </div>

            {/* Database Card */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">Culinary Knowledge DB</h4>
                    <p className="text-xs text-slate-400">SQLite + FTS5 + Vec RAG</p>
                  </div>
                </div>
                {getStatusBadge(health?.services.database?.status)}
              </div>
              <div className="text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                {health?.services.database ? (
                  <span>{health.services.database.message}</span>
                ) : (
                  <span>Checking SQLite storage...</span>
                )}
              </div>
            </div>

            {/* Model Card */}
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-slate-100">Local VLM Engine</h4>
                    <p className="text-xs text-slate-400">Ollama (Qwen3-VL:8b)</p>
                  </div>
                </div>
                {getStatusBadge(health?.services.model_service?.status)}
              </div>
              <div className="text-xs text-slate-400 border-t border-slate-800/60 pt-3">
                {health?.services.model_service ? (
                  <span>{health.services.model_service.message}</span>
                ) : (
                  <span>Testing Ollama connection...</span>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Safety Rule Callout */}
        <section className="p-5 rounded-2xl bg-gradient-to-r from-amber-500/10 via-amber-600/5 to-transparent border border-amber-500/20 flex items-start gap-4">
          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div className="flex flex-col gap-1 text-xs sm:text-sm">
            <h4 className="font-semibold text-amber-200">Critical Allergen Safety Rule</h4>
            <p className="text-slate-300 leading-relaxed">
              Never present an inferred allergen absence as proof that a dish is safe. Use verified restaurant recipe records as the authoritative source when available, distinguishing between <span className="font-semibold text-emerald-400">confirmed</span>, <span className="font-semibold text-amber-400">possible</span>, and <span className="font-semibold text-slate-400">unknown</span> ingredients.
            </p>
          </div>
        </section>

        {/* Roadmap tracker */}
        <section className="flex flex-col gap-4">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
            Development Phase Roadmap
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {PHASES.map((phase) => (
              <div
                key={phase.id}
                className={`p-3.5 rounded-xl border text-xs flex items-center justify-between ${
                  phase.status === "completed"
                    ? "bg-indigo-950/30 border-indigo-500/40 text-indigo-200"
                    : "bg-slate-900/30 border-slate-800/60 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-2.5 truncate">
                  <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-mono font-bold text-[10px] text-slate-300">
                    {phase.id}
                  </span>
                  <span className="font-medium truncate">{phase.name}</span>
                </div>
                {phase.status === "completed" ? (
                  <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    Done
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500">Upcoming</span>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

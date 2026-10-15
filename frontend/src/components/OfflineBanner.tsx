import React, { useSyncExternalStore } from "react";
import { WifiOff, AlertTriangle, RefreshCw } from "lucide-react";

interface OfflineBannerProps {
  backendReachable?: boolean;
  modelReady?: boolean;
  onRefresh?: () => void;
}

function subscribeOnline(callback: () => void) {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("online", callback);
  window.addEventListener("offline", callback);
  return () => {
    window.removeEventListener("online", callback);
    window.removeEventListener("offline", callback);
  };
}

function getOnlineSnapshot(): boolean {
  return typeof navigator !== "undefined" && typeof navigator.onLine === "boolean"
    ? navigator.onLine
    : true;
}

function getServerSnapshot(): boolean {
  return true;
}

function getClientMounted(): boolean {
  return true;
}

function getServerMounted(): boolean {
  return false;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  backendReachable = true,
  modelReady = true,
  onRefresh,
}) => {
  const isMounted = useSyncExternalStore(subscribeOnline, getClientMounted, getServerMounted);
  const isOnline = useSyncExternalStore(subscribeOnline, getOnlineSnapshot, getServerSnapshot);

  // Avoid hydration mismatch while mounting on client
  if (!isMounted) {
    return null;
  }

  // When backend and local vision model are healthy, the local AI lens is fully operational
  if (backendReachable && modelReady) {
    return null;
  }

  return (
    <div
      role="alert"
      className="w-full bg-amber-500/15 border-b border-amber-500/30 px-4 py-2.5 text-xs text-amber-200 flex items-center justify-between gap-3 shadow-sm backdrop-blur-md"
    >
      <div className="flex items-center gap-2">
        {!backendReachable ? (
          <>
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Local Backend Offline:</strong> FastAPI backend is unreachable at port 8001. Ensure the server is running (`python -m uvicorn backend.app.main:app --port 8001`).
            </span>
          </>
        ) : !modelReady ? (
          <>
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Local Vision Model Offline:</strong> Model `qwen3-vl:8b` is not ready. Ensure Ollama is running (`ollama run qwen3-vl:8b`).
            </span>
          </>
        ) : !isOnline ? (
          <>
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Offline Mode Active:</strong> App shell is loaded from PWA cache. Live vision analysis requires connectivity to your local Ollama server.
            </span>
          </>
        ) : null}
      </div>

      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/20 hover:bg-amber-500/30 text-amber-100 font-medium transition-colors shrink-0"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};

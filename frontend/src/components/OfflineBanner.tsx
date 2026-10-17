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
      className="w-full bg-[#FCF5EB] border-b border-[#F0D6AF] px-4 py-2.5 text-xs text-[#9B6416] flex items-center justify-between gap-3 shadow-sm"
    >
      <div className="flex items-center gap-2">
        {!backendReachable ? (
          <>
            <AlertTriangle className="w-4 h-4 text-[#9B6416] shrink-0" />
            <span>
              <strong className="font-bold">Local Backend Offline:</strong> FastAPI backend is unreachable at port 8001. Ensure the server is running (`python -m uvicorn backend.app.main:app --port 8001`).
            </span>
          </>
        ) : !modelReady ? (
          <>
            <AlertTriangle className="w-4 h-4 text-[#9B6416] shrink-0" />
            <span>
              <strong className="font-bold">Local Vision Model Offline:</strong> Model `qwen3-vl:8b` is not ready. Ensure Ollama is running (`ollama run qwen3-vl:8b`).
            </span>
          </>
        ) : !isOnline ? (
          <>
            <WifiOff className="w-4 h-4 text-[#9B6416] shrink-0" />
            <span>
              <strong className="font-bold">Offline Mode Active:</strong> App shell is loaded from PWA cache. Live vision analysis requires connectivity to your local Ollama server.
            </span>
          </>
        ) : null}
      </div>

      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#F2DFD3] hover:bg-[#EADFD5] text-[#1F1B18] font-semibold transition-colors shrink-0 border border-[#EADFD5]"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
};

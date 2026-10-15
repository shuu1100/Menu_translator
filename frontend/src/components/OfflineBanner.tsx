"use client";

import React, { useState, useEffect } from "react";
import { WifiOff, AlertTriangle, RefreshCw } from "lucide-react";

interface OfflineBannerProps {
  backendReachable?: boolean;
  modelReady?: boolean;
  onRefresh?: () => void;
}

export const OfflineBanner: React.FC<OfflineBannerProps> = ({
  backendReachable = true,
  modelReady = true,
  onRefresh,
}) => {
  const [isOnline, setIsOnline] = useState(() =>
    typeof navigator !== "undefined" ? navigator.onLine : true
  );

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline && backendReachable && modelReady) {
    return null;
  }

  return (
    <div
      role="alert"
      className="w-full bg-amber-500/15 border-b border-amber-500/30 px-4 py-2.5 text-xs text-amber-200 flex items-center justify-between gap-3 shadow-sm backdrop-blur-md"
    >
      <div className="flex items-center gap-2">
        {!isOnline ? (
          <>
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Offline Mode Active:</strong> App shell is loaded from PWA cache. Live vision analysis requires network connectivity to your local Ollama server.
            </span>
          </>
        ) : !backendReachable ? (
          <>
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Local Backend Offline:</strong> FastAPI backend is unreachable at port 8000. You can explore pre-loaded sample menus in the meantime.
            </span>
          </>
        ) : (
          <>
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <strong>Local Vision Model Offline:</strong> Ensure Ollama is running (`ollama run qwen3-vl:8b`) for live camera menu extraction.
            </span>
          </>
        )}
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

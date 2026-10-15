/**
 * Typed API Client for Menu Translator Backend.
 * Handles timeouts, cancellation, correlation IDs, and unified error mapping.
 */

import { MenuAnalysisResponse, SupportedLanguage } from "../types/menu";

export interface AnalyzeMenuOptions {
  file: File | Blob;
  targetLanguage: SupportedLanguage;
  dietaryRestrictions?: string[];
  restaurantId?: string;
  applyClahe?: boolean;
  timeoutMs?: number;
  signal?: AbortSignal;
}

export interface ApiClientError {
  code: string;
  message: string;
  status: number;
  details?: Record<string, unknown>;
}

export class MenuTranslatorApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl =
      baseUrl ||
      (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) ||
      "http://127.0.0.1:8001";
  }

  /**
   * Check system health and service dependencies (DB, Ollama).
   */
  async getHealth(signal?: AbortSignal): Promise<{
    status: string;
    services: {
      api?: { status: string; message: string };
      database?: { status: string; message: string };
      model_service?: { status: string; message: string };
    };
  }> {
    const res = await fetch(`${this.baseUrl}/health`, {
      method: "GET",
      cache: "no-store",
      signal,
    });

    if (!res.ok) {
      throw {
        code: "HEALTH_CHECK_FAILED",
        message: `Health check returned HTTP ${res.status}`,
        status: res.status,
      } as ApiClientError;
    }

    return res.json();
  }

  /**
   * Fetch supported target languages from backend.
   */
  async getSupportedLanguages(signal?: AbortSignal): Promise<{
    languages: Array<{ code: string; name: string }>;
  }> {
    const res = await fetch(`${this.baseUrl}/api/v1/menus/supported-languages`, {
      method: "GET",
      signal,
    });

    if (!res.ok) {
      throw {
        code: "LANGUAGES_FETCH_FAILED",
        message: `Failed to fetch languages (HTTP ${res.status})`,
        status: res.status,
      } as ApiClientError;
    }

    return res.json();
  }

  /**
   * Execute full visual menu analysis pipeline.
   */
  async analyzeMenu(options: AnalyzeMenuOptions): Promise<MenuAnalysisResponse> {
    const {
      file,
      targetLanguage,
      dietaryRestrictions = [],
      restaurantId,
      applyClahe = false,
      timeoutMs = 120000,
      signal,
    } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    if (signal) {
      signal.addEventListener("abort", () => controller.abort());
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_language", targetLanguage);

    if (dietaryRestrictions.length > 0) {
      dietaryRestrictions.forEach((r) => {
        formData.append("dietary_restrictions", r);
      });
    }

    if (restaurantId) {
      formData.append("restaurant_id", restaurantId);
    }

    if (applyClahe) {
      formData.append("apply_clahe", "true");
    }

    try {
      const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      const res = await fetch(`${this.baseUrl}/api/v1/menus/analyze`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
        headers: {
          "X-Client-Request-ID": requestId,
        },
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        let errData: Record<string, unknown> = {};
        try {
          errData = (await res.json()) as Record<string, unknown>;
        } catch {
          // non-JSON error
        }

        const errDetail = errData?.detail as Record<string, unknown> | undefined;
        const errObj = errData?.error as Record<string, unknown> | undefined;

        const code =
          (errDetail?.code as string) ||
          (errObj?.code as string) ||
          `HTTP_${res.status}`;
        const message =
          (errDetail?.message as string) ||
          (errObj?.message as string) ||
          `Server responded with HTTP ${res.status}`;

        throw {
          code,
          message,
          status: res.status,
          details: (errDetail || errObj) as Record<string, unknown> | undefined,
        } as ApiClientError;
      }

      return (await res.json()) as MenuAnalysisResponse;
    } catch (err: unknown) {
      clearTimeout(timeoutId);

      if (err && typeof err === "object" && "status" in err) {
        throw err;
      }

      const isAbort = (err as Error)?.name === "AbortError";
      throw {
        code: isAbort ? "REQUEST_TIMEOUT" : "NETWORK_ERROR",
        message: isAbort
          ? `Analysis request timed out after ${timeoutMs / 1000}s.`
          : (err as Error)?.message || "Failed to communicate with Menu Translator backend.",
        status: isAbort ? 504 : 0,
      } as ApiClientError;
    }
  }
}

export const apiClient = new MenuTranslatorApiClient();

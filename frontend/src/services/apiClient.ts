/**
 * Typed API Client for Menu Translator Backend.
 * Handles timeouts, cancellation, correlation IDs, and unified error mapping.
 */

import { AnalyzedDish, DishImageInfo, MenuAnalysisResponse, SupportedLanguage } from "../types/menu";

export interface AnalyzeMenuOptions {
  file: File | Blob;
  targetLanguage: SupportedLanguage;
  dietaryRestrictions?: string[];
  restaurantId?: string;
  applyClahe?: boolean;
  rotation?: number;
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

  private getCandidateBaseUrls(): string[] {
    const candidates = [this.baseUrl];
    if (typeof window !== "undefined") {
      const host = window.location.hostname || "127.0.0.1";
      candidates.push(`http://${host}:8001`);
      candidates.push("http://127.0.0.1:8001");
      candidates.push("http://localhost:8001");
    }
    return Array.from(new Set(candidates));
  }

  /**
   * Check system health and service dependencies (DB, Ollama).
   * Supports auto-discovery across candidate ports (8001, 8000, 127.0.0.1, localhost).
   */
  async getHealth(signal?: AbortSignal): Promise<{
    status: string;
    services: {
      api?: { status: string; message: string };
      database?: { status: string; message: string };
      model_service?: { status: string; message: string };
    };
  }> {
    const uniqueCandidates = this.getCandidateBaseUrls();

    let lastError: unknown = null;
    for (const candidate of uniqueCandidates) {
      try {
        const res = await fetch(`${candidate}/health`, {
          method: "GET",
          cache: "no-store",
          signal,
        });

        if (res.ok) {
          this.baseUrl = candidate;
          return await res.json();
        }
      } catch (err) {
        lastError = err;
      }
    }

    throw {
      code: "HEALTH_CHECK_FAILED",
      message: `Health check failed across all endpoints: ${lastError}`,
      status: 503,
    } as ApiClientError;
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
      timeoutMs = 300000,
      signal,
    } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    if (signal) {
      signal.addEventListener("abort", () => controller.abort());
    }

    const candidateUrls = this.getCandidateBaseUrls();
    let lastError: unknown = null;

    for (let i = 0; i < candidateUrls.length; i++) {
      const currentUrl = candidateUrls[i];

      const formData = new FormData();
      formData.append("file", file);
      formData.append("target_language", targetLanguage);

      if (dietaryRestrictions.length > 0) {
        const serialized = JSON.stringify(dietaryRestrictions);
        formData.append("user_dietary_restrictions", serialized);
        formData.append("dietary_restrictions", serialized);
      }

      if (restaurantId) {
        formData.append("restaurant_id", restaurantId);
      }

      if (applyClahe) {
        formData.append("apply_clahe", "true");
      }

      if (options.rotation !== undefined && options.rotation !== null) {
        formData.append("rotation", String(options.rotation));
      }

      try {
        const requestId = `req_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
        const res = await fetch(`${currentUrl}/api/v1/menus/analyze`, {
          method: "POST",
          body: formData,
          signal: controller.signal,
          headers: {
            "X-Client-Request-ID": requestId,
          },
        });

        clearTimeout(timeoutId);
        this.baseUrl = currentUrl;

        if (!res.ok) {
          let errData: Record<string, unknown> = {};
          try {
            errData = (await res.json()) as Record<string, unknown>;
          } catch {
            // non-JSON error
          }

          const errObj = errData?.error as Record<string, unknown> | undefined;
          const errDetail = errData?.detail;
          let detailMsg: string | undefined;
          let detailCode: string | undefined;

          if (typeof errDetail === "string") {
            detailMsg = errDetail;
          } else if (errDetail && typeof errDetail === "object" && !Array.isArray(errDetail)) {
            const d = errDetail as Record<string, unknown>;
            detailMsg = (d.message as string) || (d.error as string);
            detailCode = d.code as string;
          } else if (Array.isArray(errDetail) && errDetail.length > 0) {
            detailMsg = (errDetail as Array<Record<string, unknown>>)
              .map((e) => (e.msg as string) || (e.message as string) || JSON.stringify(e))
              .join("; ");
            detailCode = "VALIDATION_ERROR";
          }

          const code =
            (errObj?.code as string) ||
            detailCode ||
            `HTTP_${res.status}`;
          const message =
            (errObj?.message as string) ||
            detailMsg ||
            `Server responded with HTTP ${res.status}`;

          throw {
            code,
            message,
            status: res.status,
            details: (errObj || (typeof errDetail === "object" ? errDetail : { detail: errDetail })) as Record<string, unknown> | undefined,
          } as ApiClientError;
        }

        return (await res.json()) as MenuAnalysisResponse;
      } catch (err: unknown) {
        const isAbort = (err as Error)?.name === "AbortError";
        // If it's a known HTTP error or abort/timeout, or last candidate, rethrow
        if (isAbort || (err && typeof err === "object" && "status" in err && (err as { status: number }).status > 0)) {
          clearTimeout(timeoutId);
          throw err;
        }

        lastError = err;
        // If we have more candidates to try on network failure, proceed to next candidate
        if (i < candidateUrls.length - 1) {
          console.warn(`[MenuTranslator] Connection to ${currentUrl} failed, trying ${candidateUrls[i + 1]}...`);
          continue;
        }
      }
    }

    clearTimeout(timeoutId);
    throw {
      code: "NETWORK_ERROR",
      message: (lastError as Error)?.message || "Failed to communicate with Menu Translator backend on port 8001.",
      status: 0,
    } as ApiClientError;
  }

  /**
   * Retranslate existing dishes without re-uploading the photo.
   */
  async retranslateMenu(options: {
    dishes: AnalyzedDish[];
    targetLanguage: SupportedLanguage;
    userRestrictions?: string[];
  }): Promise<{ dishes: AnalyzedDish[]; target_language: string }> {
    const res = await fetch(`${this.baseUrl}/api/v1/menus/retranslate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dishes: options.dishes,
        target_language: options.targetLanguage,
        user_dietary_restrictions: options.userRestrictions || [],
      }),
    });

    if (!res.ok) {
      let errData: Record<string, unknown> = {};
      try {
        errData = (await res.json()) as Record<string, unknown>;
      } catch {
        // non-JSON
      }
      const errDetail = errData?.detail as Record<string, unknown> | undefined;
      throw {
        code: (errDetail?.code as string) || `HTTP_${res.status}`,
        message: (errDetail?.message as string) || `Retranslation failed (HTTP ${res.status})`,
        status: res.status,
      } as ApiClientError;
    }

    return res.json();
  }

  /**
   * Search for a representative food image for a single dish.
   */
  async searchDishImage(params: {
    dishName: string;
    dishId?: string;
    nativeName?: string;
    transliteration?: string;
    cuisine?: string;
    section?: string;
    signal?: AbortSignal;
  }): Promise<DishImageInfo> {
    const url = new URL(`${this.baseUrl}/api/v1/images/search`);
    url.searchParams.set("dish_name", params.dishName);
    if (params.dishId) url.searchParams.set("dish_id", params.dishId);
    if (params.nativeName) url.searchParams.set("native_name", params.nativeName);
    if (params.transliteration) url.searchParams.set("transliteration", params.transliteration);
    if (params.cuisine) url.searchParams.set("cuisine", params.cuisine);
    if (params.section) url.searchParams.set("section", params.section);

    const res = await fetch(url.toString(), {
      method: "GET",
      signal: params.signal,
    });

    if (!res.ok) {
      throw {
        code: `HTTP_${res.status}`,
        message: `Image search failed (HTTP ${res.status})`,
        status: res.status,
      } as ApiClientError;
    }

    return res.json();
  }

  /**
   * Batch search representative food images for an entire extracted menu.
   */
  async batchSearchDishImages(options: {
    dishes: Array<{
      dish_id: string;
      dish_name: string;
      native_name?: string | null;
      transliteration?: string | null;
      cuisine?: string | null;
      section?: string | null;
      ingredients?: string[];
    }>;
    cuisine?: string;
    signal?: AbortSignal;
  }): Promise<{
    results: Record<string, DishImageInfo>;
    total_requested: number;
    total_matched: number;
    provider_used: string;
  }> {
    const res = await fetch(`${this.baseUrl}/api/v1/images/batch-search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        dishes: options.dishes,
        cuisine: options.cuisine,
      }),
      signal: options.signal,
    });

    if (!res.ok) {
      throw {
        code: `HTTP_${res.status}`,
        message: `Batch image search failed (HTTP ${res.status})`,
        status: res.status,
      } as ApiClientError;
    }

    return res.json();
  }
}

export const apiClient = new MenuTranslatorApiClient();

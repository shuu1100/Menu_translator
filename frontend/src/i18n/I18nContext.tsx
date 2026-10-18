"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { SupportedLanguage } from "../types/menu";

// Import pre-compiled local dictionaries (no network delay or API dependency)
import en from "../messages/en.json";
import es from "../messages/es.json";
import fr from "../messages/fr.json";
import de from "../messages/de.json";
import hi from "../messages/hi.json";
import ja from "../messages/ja.json";
import ko from "../messages/ko.json";
import zh from "../messages/zh.json";
import it from "../messages/it.json";
import pt from "../messages/pt.json";
import ru from "../messages/ru.json";
import ar from "../messages/ar.json";

// Type definition for nested dictionary
type TranslationDict = Record<string, any>;

const DICTIONARIES: Record<SupportedLanguage, TranslationDict> = {
  en,
  es,
  fr,
  de,
  hi,
  ja,
  ko,
  zh,
  "zh-CN": zh,
  it,
  pt,
  ru,
  ar,
};

const RTL_LANGUAGES: SupportedLanguage[] = ["ar"];

interface I18nContextType {
  uiLanguage: SupportedLanguage;
  setUiLanguage: (lang: SupportedLanguage) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
  isRtl: boolean;
}

const I18nContext = createContext<I18nContextType>({
  uiLanguage: "en",
  setUiLanguage: () => {},
  t: (key: string) => key,
  isRtl: false,
});

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Start with 'en' to guarantee identical SSR and initial client hydration
  const [uiLanguage, setUiLanguageState] = useState<SupportedLanguage>("en");
  const [isHydrated, setIsHydrated] = useState(false);

  // Restore saved UI language preference on client mount
  useEffect(() => {
    setIsHydrated(true);
    try {
      const saved = localStorage.getItem("menu_translator_ui_lang");
      if (saved && saved in DICTIONARIES) {
        setUiLanguageState(saved as SupportedLanguage);
      } else {
        // Optional: match browser language if supported
        const browserLang = navigator.language.split("-")[0]?.toLowerCase();
        if (browserLang && browserLang in DICTIONARIES) {
          setUiLanguageState(browserLang as SupportedLanguage);
        }
      }
    } catch {
      // Ignore localStorage read errors
    }
  }, []);

  // Update HTML lang and dir attributes whenever uiLanguage changes
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = uiLanguage;
      document.documentElement.dir = RTL_LANGUAGES.includes(uiLanguage) ? "rtl" : "ltr";
    }
  }, [uiLanguage]);

  const setUiLanguage = useCallback((lang: SupportedLanguage) => {
    setUiLanguageState(lang);
    try {
      localStorage.setItem("menu_translator_ui_lang", lang);
    } catch {
      // Ignore localStorage write errors
    }
  }, []);

  // Helper to look up key in dictionary with dot-notation
  const getNestedValue = (obj: any, path: string): string | undefined => {
    const parts = path.split(".");
    let current = obj;
    for (const part of parts) {
      if (current === null || current === undefined || typeof current !== "object") {
        return undefined;
      }
      current = current[part];
    }
    return typeof current === "string" ? current : undefined;
  };

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      const dict = DICTIONARIES[uiLanguage] || DICTIONARIES.en;
      let rawText = getNestedValue(dict, key);

      // Fallback to English dictionary if key is missing in active language
      if (rawText === undefined && uiLanguage !== "en") {
        rawText = getNestedValue(DICTIONARIES.en, key);
      }

      // Final fallback to key itself if not found anywhere
      if (rawText === undefined) {
        return key;
      }

      // Interpolate parameters: {paramName} -> paramValue
      if (params) {
        return rawText.replace(/\{([a-zA-Z0-9_]+)\}/g, (match, paramName) => {
          if (paramName in params) {
            return String(params[paramName]);
          }
          return match;
        });
      }

      return rawText;
    },
    [uiLanguage]
  );

  const isRtl = useMemo(() => RTL_LANGUAGES.includes(uiLanguage), [uiLanguage]);

  const contextValue = useMemo(
    () => ({
      uiLanguage,
      setUiLanguage,
      t,
      isRtl,
    }),
    [uiLanguage, setUiLanguage, t, isRtl]
  );

  return <I18nContext.Provider value={contextValue}>{children}</I18nContext.Provider>;
};

export const useTranslation = () => useContext(I18nContext);

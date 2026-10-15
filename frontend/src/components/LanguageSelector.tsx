"use client";

import React from "react";
import { SupportedLanguage } from "../types/menu";
import { Globe } from "lucide-react";

interface LanguageOption {
  code: SupportedLanguage;
  name: string;
  nativeName: string;
  isRtl?: boolean;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: "en", name: "English", nativeName: "English" },
  { code: "es", name: "Spanish", nativeName: "Español" },
  { code: "fr", name: "French", nativeName: "Français" },
  { code: "de", name: "German", nativeName: "Deutsch" },
  { code: "it", name: "Italian", nativeName: "Italiano" },
  { code: "ja", name: "Japanese", nativeName: "日本語" },
  { code: "zh", name: "Chinese", nativeName: "中文" },
  { code: "ar", name: "Arabic", nativeName: "العربية", isRtl: true },
  { code: "pt", name: "Portuguese", nativeName: "Português" },
  { code: "ko", name: "Korean", nativeName: "한국어" },
];

interface LanguageSelectorProps {
  value: SupportedLanguage;
  onChange: (language: SupportedLanguage) => void;
  disabled?: boolean;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="flex items-center gap-2">
      <div className="relative inline-flex items-center">
        <Globe className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
        <select
          value={value}
          onChange={(e) => onChange(e.target.value as SupportedLanguage)}
          disabled={disabled}
          aria-label="Target Translation Language"
          className="appearance-none bg-slate-900 border border-slate-700/80 hover:border-slate-600 rounded-xl pl-9 pr-8 py-2 text-xs sm:text-sm font-medium text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-inner"
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code} className="bg-slate-900 text-slate-100">
              {lang.nativeName} ({lang.name})
            </option>
          ))}
        </select>
        <div className="absolute right-3 pointer-events-none text-slate-400 text-[10px]">
          ▼
        </div>
      </div>
    </div>
  );
};

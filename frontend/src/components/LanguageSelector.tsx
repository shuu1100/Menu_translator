"use client";

import React from "react";
import { SupportedLanguage } from "../types/menu";
import { Globe, ChevronDown } from "lucide-react";

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
  { code: "hi", name: "Hindi", nativeName: "हिन्दी" },
  { code: "ru", name: "Russian", nativeName: "Русский" },
];

interface LanguageSelectorProps {
  value: SupportedLanguage;
  onChange: (language: SupportedLanguage) => void;
  disabled?: boolean;
  className?: string;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  className = "",
}) => {
  return (
    <div className={`flex items-center ${className}`}>
      <div className="relative inline-flex items-center w-full">
        <Globe className="w-4 h-4 text-[#C74735] absolute left-3 pointer-events-none" />
        <select
          value={value}
          onChange={(e) => onChange(e.target.value as SupportedLanguage)}
          disabled={disabled}
          aria-label="Target Translation Language"
          className="w-full appearance-none bg-white border border-[#EADFD5] hover:border-[#8C716C]/40 rounded-full pl-9 pr-8 py-2 text-xs sm:text-sm font-semibold text-[#1F1B18] focus:outline-none focus:ring-2 focus:ring-[#C74735]/25 focus:border-[#C74735] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_1px_3px_rgba(41,37,34,0.04)]"
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code} className="bg-white text-[#1F1B18] py-1">
              {lang.nativeName} ({lang.name})
            </option>
          ))}
        </select>
        <ChevronDown className="w-3.5 h-3.5 absolute right-3 pointer-events-none text-[#58413D]" />
      </div>
    </div>
  );
};

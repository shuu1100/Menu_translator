"use client";

import React from "react";
import { ShieldAlert, Check } from "lucide-react";
import { useTranslation } from "../i18n/I18nContext";

export interface DietaryOption {
  id: string;
  label: string;
  category: "diet" | "allergen";
  iconText?: string;
}

export const DIETARY_OPTIONS: DietaryOption[] = [
  { id: "gluten", label: "Gluten-Free", category: "allergen", iconText: "🌾" },
  { id: "dairy", label: "Dairy-Free", category: "allergen", iconText: "🥛" },
  { id: "vegan", label: "Vegan", category: "diet", iconText: "🌱" },
  { id: "vegetarian", label: "Vegetarian", category: "diet", iconText: "🥗" },
  { id: "peanuts", label: "Peanuts", category: "allergen", iconText: "🥜" },
  { id: "tree_nuts", label: "Tree Nuts", category: "allergen", iconText: "🌰" },
  { id: "shellfish", label: "Shellfish", category: "allergen", iconText: "🦐" },
  { id: "fish", label: "Fish", category: "allergen", iconText: "🐟" },
  { id: "soy", label: "Soy", category: "allergen", iconText: "🫘" },
  { id: "halal", label: "Halal", category: "diet", iconText: "🌙" },
];

interface DietaryPreferencesSelectorProps {
  selected: string[];
  onChange: (selected: string[]) => void;
  compact?: boolean;
}

export const DietaryPreferencesSelector: React.FC<DietaryPreferencesSelectorProps> = ({
  selected,
  onChange,
  compact = false,
}) => {
  const { t } = useTranslation();
  const toggleRestriction = (id: string) => {
    if (selected.includes(id)) {
      onChange(selected.filter((item) => item !== id));
    } else {
      onChange([...selected, id]);
    }
  };

  const clearAll = () => {
    onChange([]);
  };

  return (
    <div className="flex flex-col gap-2.5">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold text-[#58413D] uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-[#9B6416]" />
          {t("dietary.title")}
        </label>
        {selected.length > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="text-[11px] font-semibold text-[#A52F20] hover:text-[#C74735] underline cursor-pointer"
          >
            {t("dietary.clearAll") || "Clear all"} ({selected.length})
          </button>
        )}
      </div>

      <div className={`flex flex-wrap gap-1.5 ${compact ? "max-h-24 overflow-y-auto" : ""}`}>
        {DIETARY_OPTIONS.map((opt) => {
          const isSelected = selected.includes(opt.id);
          const localizedLabel = t(`dietary.${opt.id}`) || opt.label;
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => toggleRestriction(opt.id)}
              aria-pressed={isSelected}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer shadow-[0_1px_3px_rgba(41,37,34,0.03)] active:scale-95 ${
                isSelected
                  ? "bg-[#F2DFD3] text-[#A52F20] border border-[#C74735] shadow-sm"
                  : "bg-white text-[#58413D] border border-[#EADFD5] hover:border-[#8C716C]/40 hover:bg-[#FBF2ED]"
              }`}
            >
              <span>{opt.iconText}</span>
              <span>{localizedLabel}</span>
              {isSelected && <Check className="w-3 h-3 text-[#A52F20] stroke-[2.5]" />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

"use client";

import React from "react";
import { ShieldAlert, Check } from "lucide-react";

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
        <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
          Dietary Restrictions & Allergens
        </label>
        {selected.length > 0 && (
          <button
            type="button"
            onClick={clearAll}
            className="text-[11px] text-slate-400 hover:text-slate-200 underline cursor-pointer"
          >
            Clear all ({selected.length})
          </button>
        )}
      </div>

      <div className={`flex flex-wrap gap-1.5 ${compact ? "max-h-24 overflow-y-auto" : ""}`}>
        {DIETARY_OPTIONS.map((opt) => {
          const isSelected = selected.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => toggleRestriction(opt.id)}
              aria-pressed={isSelected}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                isSelected
                  ? "bg-amber-500/20 text-amber-300 border border-amber-500/50 shadow-sm shadow-amber-500/10"
                  : "bg-slate-900/80 text-slate-400 border border-slate-800 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              <span>{opt.iconText}</span>
              <span>{opt.label}</span>
              {isSelected && <Check className="w-3 h-3 text-amber-400 stroke-[2.5]" />}
            </button>
          );
        })}
      </div>
    </div>
  );
};

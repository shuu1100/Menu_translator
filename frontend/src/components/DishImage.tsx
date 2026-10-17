"use client";

import React, { useState, useEffect } from "react";
import { ImageIcon, RefreshCw, ExternalLink, Info } from "lucide-react";
import { DishImageInfo } from "../types/menu";

interface DishImageProps {
  imageInfo?: DishImageInfo | null;
  dishName: string;
  className?: string;
  aspectRatioClass?: string;
  showAttribution?: boolean;
  onRetry?: () => void;
  priority?: boolean;
}

export const DishImage: React.FC<DishImageProps> = ({
  imageInfo,
  dishName,
  className = "",
  aspectRatioClass = "aspect-[16/10]",
  showAttribution = true,
  onRetry,
  priority = false,
}) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  // Reset loading and error states whenever image URL changes
  useEffect(() => {
    setImageLoaded(false);
    setHasError(false);
  }, [imageInfo?.image_url]);

  const isUnavailable = !imageInfo || imageInfo.status === "unavailable" || imageInfo.is_fallback || hasError;
  const imageUrl = hasError ? null : imageInfo?.image_url;

  return (
    <div
      className={`relative w-full overflow-hidden rounded-xl bg-[#F5ECE7] border border-[#EADFD5] group select-none ${aspectRatioClass} ${className}`}
    >
      {/* 1. Loading Skeleton / Shimmer */}
      {!imageLoaded && !isUnavailable && (
        <div className="absolute inset-0 bg-gradient-to-r from-[#F5ECE7] via-[#FFF8F5] to-[#F5ECE7] animate-pulse flex items-center justify-center">
          <div className="flex flex-col items-center gap-1.5 opacity-40">
            <ImageIcon className="w-6 h-6 text-[#70645C]" />
            <span className="text-[10px] font-semibold text-[#70645C]">Matching photo...</span>
          </div>
        </div>
      )}

      {/* 2. Image Element */}
      {imageUrl && !hasError ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={imageUrl}
          alt={imageInfo?.alt_text || `Representative food photo of ${dishName}`}
          loading={priority ? "eager" : "lazy"}
          onLoad={() => setImageLoaded(true)}
          onError={() => {
            setHasError(true);
            setImageLoaded(true);
          }}
          className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${
            imageLoaded ? "opacity-100" : "opacity-0"
          }`}
        />
      ) : (
        /* 3. Neutral Fallback Placeholder */
        <div className="absolute inset-0 flex flex-col items-center justify-center p-3 text-center bg-[#FBF2ED]">
          <div className="w-9 h-9 rounded-full bg-[#F2DFD3] flex items-center justify-center text-[#C74735] mb-1.5 shadow-xs">
            <ImageIcon className="w-4 h-4 text-[#C74735]" />
          </div>
          <span className="text-[11px] font-bold text-[#1F1B18] line-clamp-1">
            {dishName}
          </span>
          <span className="text-[10px] text-[#70645C] mt-0.5 font-medium">
            Representative photo unavailable
          </span>
          {onRetry && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setHasError(false);
                setImageLoaded(false);
                onRetry();
              }}
              className="mt-2 inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold bg-[#FFF8F5] hover:bg-[#F2DFD3] text-[#C74735] border border-[#EADFD5] shadow-xs cursor-pointer transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
              <span>Retry</span>
            </button>
          )}
        </div>
      )}

      {/* 4. Subtle Overlay Badges when Image is Available */}
      {imageUrl && !hasError && imageLoaded && (
        <>
          {/* Subtle gradient scrim at top and bottom */}
          <div className="absolute inset-x-0 bottom-0 h-10 bg-gradient-to-t from-black/60 via-black/20 to-transparent pointer-events-none" />

          {/* Top Representative Badge */}
          <div className="absolute top-2 left-2 z-10 flex items-center gap-1">
            <span
              title="Online culinary reference photo. Not the restaurant's actual serving."
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#1F1B18]/75 backdrop-blur-md text-[10px] font-medium text-white shadow-xs border border-white/10"
            >
              <Info className="w-2.5 h-2.5 text-[#F2DFD3]" />
              <span>Representative photo • Not restaurant's actual serving</span>
            </span>
          </div>

          {/* Bottom Photographer / Source Attribution (Compliant with Unsplash API Guidelines) */}
          {showAttribution && imageInfo?.photographer && (
            <div className="absolute bottom-1.5 right-2 z-10 text-[9px] text-white/90 drop-shadow-xs flex items-center gap-1 max-w-[85%] truncate">
              {imageInfo.source === "unsplash" ? (
                <span className="truncate flex items-center gap-0.5 text-white/90">
                  Photo by{" "}
                  <a
                    href={imageInfo.photographer_url || "https://unsplash.com/?utm_source=universal_menu_translator&utm_medium=referral"}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="hover:underline font-semibold text-white ml-0.5 underline-offset-2"
                  >
                    {imageInfo.photographer}
                  </a>{" "}
                  on{" "}
                  <a
                    href={imageInfo.source_url || "https://unsplash.com/?utm_source=universal_menu_translator&utm_medium=referral"}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="hover:underline font-semibold text-white ml-0.5 underline-offset-2"
                  >
                    Unsplash
                  </a>
                </span>
              ) : imageInfo.photographer_url ? (
                <a
                  href={imageInfo.photographer_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="hover:underline truncate flex items-center gap-0.5 text-white/90 hover:text-white"
                >
                  <span>Photo: {imageInfo.photographer}</span>
                  <ExternalLink className="w-2 h-2 shrink-0 opacity-70" />
                </a>
              ) : (
                <span className="truncate">Photo: {imageInfo.photographer}</span>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

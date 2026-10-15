"use client";

import React, { useRef, useState, useEffect, useCallback } from "react";
import { AnalyzedDish } from "../types/menu";
import { AlertTriangle, CheckCircle2, HelpCircle, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface MenuCanvasOverlayProps {
  imageUrl: string;
  dishes: AnalyzedDish[];
  selectedDish: AnalyzedDish | null;
  onSelectDish: (dish: AnalyzedDish | null) => void;
  userRestrictions?: string[];
}

interface ImageBoxGeometry {
  offsetX: number;
  offsetY: number;
  renderedWidth: number;
  renderedHeight: number;
}

export const MenuCanvasOverlay: React.FC<MenuCanvasOverlayProps> = ({
  imageUrl,
  dishes,
  selectedDish,
  onSelectDish,
  userRestrictions = [],
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  const [geometry, setGeometry] = useState<ImageBoxGeometry | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1.0);
  const [panOffset, setPanOffset] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Compute exact letterbox dimensions so bounding boxes align seamlessly
  const updateGeometry = useCallback(() => {
    if (!containerRef.current || !imageRef.current) return;
    const container = containerRef.current;
    const image = imageRef.current;

    const cw = container.clientWidth;
    const ch = container.clientHeight;
    const nw = image.naturalWidth;
    const nh = image.naturalHeight;

    if (!cw || !ch || !nw || !nh) return;

    const containerRatio = cw / ch;
    const naturalRatio = nw / nh;

    let rw: number;
    let rh: number;
    let ox = 0;
    let oy = 0;

    if (containerRatio > naturalRatio) {
      // Height-constrained (black letterbox bars on left & right)
      rh = ch;
      rw = ch * naturalRatio;
      ox = (cw - rw) / 2;
    } else {
      // Width-constrained (black letterbox bars on top & bottom)
      rw = cw;
      rh = cw / naturalRatio;
      oy = (ch - rh) / 2;
    }

    setGeometry({
      offsetX: ox,
      offsetY: oy,
      renderedWidth: rw,
      renderedHeight: rh,
    });
  }, []);

  useEffect(() => {
    updateGeometry();
    const handleResize = () => updateGeometry();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [updateGeometry]);

  // Zoom handlers
  const handleZoomIn = () => setZoomLevel((z) => Math.min(3.0, z + 0.25));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(1.0, z - 0.25));
  const handleResetZoom = () => {
    setZoomLevel(1.0);
    setPanOffset({ x: 0, y: 0 });
  };

  // Mouse pan handling
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoomLevel <= 1.0) return;
    setIsPanning(true);
    setDragStart({ x: e.clientX - panOffset.x, y: e.clientY - panOffset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isPanning) return;
    setPanOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsPanning(false);

  // Determine dish conflict status relative to active user restrictions
  const getDishStatus = (dish: AnalyzedDish) => {
    if (userRestrictions.length === 0) {
      return { type: "neutral", text: "View Details" };
    }

    // Check user conflicts from backend or matching allergens
    const hasConflict =
      dish.dietary_compatibility.user_conflicts.some((c) =>
        userRestrictions.includes(c.toLowerCase())
      ) ||
      dish.allergen_warnings.some(
        (w) =>
          userRestrictions.includes(w.allergen.toLowerCase()) &&
          (w.status === "confirmed" || w.status === "possible")
      );

    if (hasConflict) {
      return { type: "conflict", text: "Dietary Conflict" };
    }

    // If verified safe
    if (dish.evidence_status === "confirmed") {
      return { type: "safe", text: "Compatible" };
    }

    return { type: "unverified", text: "Unverified" };
  };

  return (
    <div className="relative w-full h-[65vh] sm:h-[75vh] bg-slate-950 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col select-none">
      {/* Zoom / Navigation Toolbar */}
      <div className="absolute top-4 right-4 z-30 flex items-center gap-1.5 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-1.5 rounded-xl shadow-lg">
        <button
          type="button"
          onClick={handleZoomIn}
          title="Zoom In"
          aria-label="Zoom in menu"
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={handleZoomOut}
          title="Zoom Out"
          aria-label="Zoom out menu"
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={handleResetZoom}
          title="Reset View"
          aria-label="Reset zoom and position"
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
        <div className="text-[10px] font-mono font-medium text-slate-400 px-2">
          {Math.round(zoomLevel * 100)}%
        </div>
      </div>

      {/* Main Canvas Area */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={(e) => {
          // If clicked canvas background, deselect
          if (e.target === containerRef.current || e.target === imageRef.current) {
            onSelectDish(null);
          }
        }}
        className={`relative w-full h-full flex items-center justify-center overflow-hidden bg-slate-950 ${
          zoomLevel > 1.0 ? "cursor-grab active:cursor-grabbing" : "cursor-default"
        }`}
      >
        <div
          style={{
            transform: `scale(${zoomLevel}) translate(${panOffset.x / zoomLevel}px, ${panOffset.y / zoomLevel}px)`,
            transformOrigin: "center center",
            transition: isPanning ? "none" : "transform 0.15s ease-out",
          }}
          className="relative w-full h-full flex items-center justify-center"
        >
          {/* Menu Image */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            ref={imageRef}
            src={imageUrl}
            alt="Original physical restaurant menu"
            onLoad={updateGeometry}
            className="w-full h-full object-contain pointer-events-none"
          />

          {/* Interactive Bounding Box Overlay Layer */}
          {geometry && (
            <div
              style={{
                position: "absolute",
                left: `${geometry.offsetX}px`,
                top: `${geometry.offsetY}px`,
                width: `${geometry.renderedWidth}px`,
                height: `${geometry.renderedHeight}px`,
              }}
              className="pointer-events-none"
            >
              {dishes.map((dish) => {
                const isSelected = selectedDish?.dish_id === dish.dish_id;
                const status = getDishStatus(dish);

                const left = dish.bounding_box.xmin * geometry.renderedWidth;
                const top = dish.bounding_box.ymin * geometry.renderedHeight;
                const width =
                  (dish.bounding_box.xmax - dish.bounding_box.xmin) *
                  geometry.renderedWidth;
                const height =
                  (dish.bounding_box.ymax - dish.bounding_box.ymin) *
                  geometry.renderedHeight;

                let borderStyle = "border-indigo-400/80 bg-indigo-500/10 text-indigo-300";
                let badgeBg = "bg-indigo-600 text-white";
                let Icon = HelpCircle;

                if (status.type === "conflict") {
                  borderStyle = "border-rose-500 bg-rose-500/20 text-rose-300 shadow-rose-500/20";
                  badgeBg = "bg-rose-600 text-white";
                  Icon = AlertTriangle;
                } else if (status.type === "safe") {
                  borderStyle = "border-emerald-400 bg-emerald-500/15 text-emerald-300 shadow-emerald-500/20";
                  badgeBg = "bg-emerald-600 text-white";
                  Icon = CheckCircle2;
                } else if (status.type === "unverified") {
                  borderStyle = "border-amber-400/90 bg-amber-500/10 text-amber-300 shadow-amber-500/15";
                  badgeBg = "bg-amber-600 text-white";
                  Icon = HelpCircle;
                }

                if (isSelected) {
                  borderStyle += " ring-2 ring-white ring-offset-2 ring-offset-slate-900";
                }

                return (
                  <button
                    key={dish.dish_id}
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectDish(dish);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        onSelectDish(dish);
                      }
                    }}
                    style={{
                      position: "absolute",
                      left: `${left}px`,
                      top: `${top}px`,
                      width: `${Math.max(width, 32)}px`,
                      height: `${Math.max(height, 28)}px`,
                    }}
                    aria-label={`Dish ${dish.reading_order}: ${dish.translated_title || dish.original_text}. Price: ${dish.price || "not listed"}. Status: ${status.text}.`}
                    className={`pointer-events-auto border-2 rounded-xl transition-all duration-150 cursor-pointer shadow-md flex flex-col justify-between p-1.5 focus:outline-none hover:scale-[1.01] ${borderStyle}`}
                  >
                    {/* Header badge inside box */}
                    <div className="flex items-center justify-between w-full pointer-events-none gap-1">
                      <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[10px] font-bold tracking-tight shadow-sm ${badgeBg}`}>
                        <Icon className="w-2.5 h-2.5" />
                        <span>#{dish.reading_order}</span>
                      </span>

                      {dish.price && (
                        <span className="px-1.5 py-0.5 rounded-md text-[10px] font-extrabold bg-slate-950/80 text-amber-300 backdrop-blur-sm border border-slate-700/80">
                          {dish.price}
                        </span>
                      )}
                    </div>

                    {/* Translated title label bar */}
                    <div className="w-full truncate text-[11px] font-semibold text-white bg-slate-950/75 backdrop-blur-sm px-1.5 py-0.5 rounded-md mt-auto text-left shadow-sm">
                      {dish.translated_title || dish.original_text}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

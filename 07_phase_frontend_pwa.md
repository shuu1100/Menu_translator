# Phase 7 Prompt --- Next.js PWA, Camera Capture, and Interactive Menu Overlay

Implement the frontend to match the uploaded design: mobile-first,
single-handed operation, original menu image as the main canvas,
interactive dish boxes, and a bottom detail drawer.

## Stack

Next.js + React + TypeScript, Tailwind CSS, Lucide icons, HTML camera
APIs, Canvas/WebGL only where useful, and PWA service-worker tooling
compatible with the current Next.js version.

## Screens and flow

1.  Landing/capture screen: app name, short privacy explanation,
    target-language selector, camera button, upload fallback.
2.  Camera screen: rear camera preferred on mobile, tap-to-focus where
    browser/device supports it, capture and retake controls. Do not
    promise focus/exposure APIs on unsupported browsers.
3.  Processing state: accessible progress messages for preprocessing,
    menu reading, knowledge lookup, translation, and validation. Use
    actual backend status if available; do not invent progress
    percentages.
4.  Results screen: original photo with overlay layer; responsive
    zoom/pan; each dish bounding box is tappable.
5.  Detail bottom sheet: native name, phonetic transcription, translated
    title, description, flavor profile, ingredients, price,
    evidence-backed allergen warnings, dietary status, and
    provenance/uncertainty.
6.  Filters: user can toggle allergens and dietary preferences; update
    visible boxes and conflict indicators.
7.  Error/recovery: retry, retake photo, upload another image, model
    unavailable, no dishes found, and network disconnected.

## Overlay requirements

-   Use the exact original image and the backend's documented coordinate
    convention.
-   Map normalized coordinates to displayed image dimensions using the
    image's actual object-fit/scale and offset. Do not position boxes
    against the entire viewport if the image is letterboxed.
-   Green/positive styling may indicate no known conflict only when
    evidence supports it; unknown status must use a distinct
    neutral/amber treatment. Red indicates a known or possible conflict.
    Include textual labels/icons for accessibility.
-   Add selection/focus states, keyboard support where appropriate, ARIA
    labels, and touch targets large enough for mobile.
-   Tapping a box opens the matching dish drawer; tapping outside closes
    it. Ensure boxes remain aligned while resizing and zooming.

## Visual direction

Use a clean, modern, high-contrast restaurant utility aesthetic. Keep
the captured menu prominent. Use readable typography, compact cards,
clear price labels, subtle transitions, and strong warning hierarchy.
Avoid clutter and avoid communicating safety through color alone.

## PWA/offline

-   Add manifest, icons/placeholders, installability, and service-worker
    caching for app shell/static assets.
-   Cache only safe static assets and optionally explicitly consented
    user preferences.
-   Do not cache private menu photos or recipe data by default.
-   If backend/model is offline, explain that the interface is available
    but AI analysis requires the local inference service to be running,
    unless true on-device inference has been implemented.
-   Do not store image data in localStorage.

## Testing

Test desktop and mobile breakpoints, long menus, image orientation, box
alignment, missing prices, long translated titles, RTL Arabic layout,
keyboard navigation, screen-reader labels, and API error states.

## Acceptance criteria

-   User can capture/upload a menu, select language/restrictions, see
    parsed bounding boxes, and open dish details.
-   Boxes line up on original image across responsive layouts.
-   Dietary filters work correctly.
-   PWA shell is installable and offline behavior is honestly
    communicated.
-   Frontend lint, type-check, and tests pass. Stop after Phase 7.

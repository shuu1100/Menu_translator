# Menu Translator — Frontend Web Application

The frontend client for Universal Menu Translator is a responsive, touch-optimized Progressive Web App (PWA) built with **Next.js 16.4.1 (Turbopack, React 19)**, TypeScript, and Tailwind CSS.

---

## 🎨 User Interface & Key Components

### 1. Main Navigation & Screen States (`src/app/page.tsx`)
- **Upload & Welcome Screen**: Clean drag-and-drop zone, camera capture button, supported formats guidance, demo menu presets, and backend health status badge.
- **Results Screen**: Dual-view toggle between **Translated Menu Cards** and interactive **Photo Canvas Overlay**.
- **Collapsible Performance Telemetry Banner**: Displays measured latency across all 8 pipeline stages, model hardware residency, tokens/second speed, and request IDs.
- **Dietary Filter Bar**: Quick restriction filter chips (`Gluten-Free`, `Dairy-Free`, `Vegan`, `Shellfish`) and instant text search.
- **Language Selector & Instant Retranslate**: Dropdown supporting 10 languages with instant re-translation (<10ms) without re-uploading the menu photo.

### 2. Camera Capture Modal (`src/components/CameraCaptureModal.tsx`)
- Integrates with device cameras via `navigator.mediaDevices.getUserMedia`.
- **90° Manual Orientation Deskew**: Diners can rotate sideways photos before triggering analysis to prevent vision model orientation distortion.
- Supports instant re-take, camera switching (front/back), and image validation.

### 3. Interactive Letterbox-Aware Photo Overlay (`src/components/MenuCanvasOverlay.tsx`)
- Renders bounding box polygons over the authentic uploaded menu photograph.
- Uses viewport letterbox-offset calculations to ensure SVG coordinates align exactly with the resized/letterboxed image.
- Supports zoom, pan, and clicking on any bounding box to open the corresponding dish detail drawer.

### 4. Dish Detail Drawer (`src/components/DishDetailDrawer.tsx`)
- Slide-out bottom sheet/side panel with deep culinary details.
- Authentic printed menu text verification box (`Original: [Printed Menu Text]`).
- Web Speech Synthesis button (`SpeechSynthesisUtterance`) to listen to native pronunciation.
- Tri-state dietary flags (vegan, vegetarian, gluten-free, halal) and evidence-grounded allergen breakdown.

### 5. API Client & Telemetry (`src/services/apiClient.ts`)
- Communicates with the FastAPI backend on `http://127.0.0.1:8001`.
- Configured with a 300-second timeout to prevent premature aborts on heavy vision inference.
- Full `AbortController` cancellation support.

---

## 🚀 Development & Build Commands

```bash
# Install dependencies
npm install

# Start development server with Turbopack (Port 3000)
npm run dev

# Run TypeScript checking & optimized production build
npm run build

# Start production server
npm start
```

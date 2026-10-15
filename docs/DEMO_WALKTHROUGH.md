# Menu Translator: Interactive Demo Walkthrough & Presentation Script

This guide outlines a step-by-step demonstration walkthrough for presentations, hackathon judging, and evaluator testing.

---

## 🎯 Demonstration Flow Overview

```
1. Landing Screen & Privacy Guarantee
      │
      ▼
2. Instant Pre-loaded Demo Menus OR Live Camera Capture
      │
      ▼
3. Transparent Pipeline Processing (5 Visual Stages)
      │
      ▼
4. Interactive Canvas Overlay (Zoom, Pan, Letterbox-Aware Alignment)
      │
      ▼
5. Multi-Sensory Conflict Highlighting (Red = Conflict, Green = Safe, Amber = Unverified)
      │
      ▼
6. Dish Detail Drawer (Phonetic Audio, Evidence Grounding, Zero False-Safe Notice)
      │
      ▼
7. PWA Offline Capability & Honest Status Communication
```

---

## 🎬 Step-by-Step Presentation Script

### Step 1: Open Application & Review Local Privacy Architecture
1. Open [http://localhost:3001](http://localhost:3001) in your browser (or install as PWA).
2. **Key Talking Point:**
   > *"Menu Translator runs 100% locally using Ollama and an embedded SQLite vector database. No menu photos are sent to cloud APIs, and no images are cached in persistent storage."*
3. Point out the **Target Language Selector** (supporting 10 languages including RTL Arabic) and the **Dietary Restrictions Selector** (e.g. toggling Gluten-Free and Dairy-Free).

---

### Step 2: Instant Demo Menu Experience (Zero Setup Required)
1. In the **"Try Pre-loaded Demo Menus"** section, click on **"Trattoria del Corso (Italian)"**.
2. **Observe:** The application immediately transitions to the interactive results screen displaying the high-resolution menu with rendered bounding boxes.
3. Notice how each dish box perfectly frames the printed text regardless of window size or screen aspect ratio due to the **letterbox-aware coordinate calculation**.

---

### Step 3: Interactive Visual Canvas Overlay
1. Test the **Zoom & Pan Controls** in the upper-right corner of the canvas:
   - Click `+` (Zoom In up to 300%)
   - Click and drag with mouse (or finger on touch devices) to pan across the menu.
   - Click Reset View to return to 100% zoom.
2. Observe the **Color & Accessible Badging**:
   - **Bruschetta al Pomodoro**: Highlighted in **Red** (`border-rose-500`) with an Alert Triangle icon and a clear textual label: *"Dietary Conflict"* (contains gluten).
   - **Tagliatelle al Ragù**: Highlighted in **Red** (contains gluten and dairy).
   - **Risotto ai Funghi Porcini**: Highlighted according to active filters.
   - **Key Talking Point:**
     > *"Safety is never communicated through color alone. Every box carries an icon, high-contrast text badge, and full ARIA button metadata for screen readers."*

---

### Step 4: Dish Detail Drawer & Evidence-Backed Disclosures
1. Click or tap directly on the **"Bruschetta al Pomodoro"** bounding box.
2. The bottom drawer (or desktop side panel) slides in smoothly:
   - **Verbatim Native Script**: *Bruschetta al Pomodoro*
   - **Phonetic Pronunciation Guide**: *broo-SKET-tah ahl poh-moh-DOH-roh*
   - **Audio Pronunciation Button**: Click the speaker icon to hear the native pronunciation synthesized via Web Speech API.
   - **Translated Title**: *Heirloom Tomato & Garlic Bruschetta*
   - **Price**: *€8.50*
   - **Cultural Context & Flavor Profile**: Crisp, aromatic garlic, sweet acidic tomato.
   - **Allergen Evidence Section**: Explicitly distinguishes between `confirmed` allergens sourced from `recipe_record` vs unverified claims.
   - **Mandatory Safety Banner**:
     > *"Zero False-Safe Mandate: Inferred absence of an allergen statement is never proof that a dish is safe."*
3. Use the **Next Dish (`→`)** button in the drawer header to smoothly step through the rest of the menu in sequential reading order.

---

### Step 5: Live Camera Scanner / Photo Upload Flow
1. Click **"New Menu"** in the top navigation to return to the capture screen.
2. Click **"Scan with Camera"**:
   - The camera capture modal opens, requesting rear camera preference (`facingMode: environment`).
   - Position a printed menu inside the viewfinder framing guide and click **"Capture Photo"**.
   - Review still snapshot, click **"Analyze Menu"**.
3. **Observe the Processing Modal**:
   - Sequential, honest status messages: *Image Optimization → Local Vision Extraction → Culinary Knowledge Lookup → Contextual Translation → Allergen & Dietary Safety*.
   - Elapsed timer shows real pipeline duration without fabricated progress percentages.

---

### Step 6: PWA Offline Demonstration
1. Open Chrome DevTools (`F12`), navigate to the **Network** tab, and toggle **Offline**.
2. Refresh the page [http://localhost:3001](http://localhost:3001).
3. **Observe:**
   - The application shell and static assets load instantly from the Service Worker cache (`/sw.js`).
   - The top banner honestly alerts the user:
     > *"Offline Mode Active: App shell is loaded from PWA cache. Live vision analysis requires network connectivity to your local Ollama server."*
   - Pre-loaded sample menus remain 100% interactive and functional even while completely disconnected!

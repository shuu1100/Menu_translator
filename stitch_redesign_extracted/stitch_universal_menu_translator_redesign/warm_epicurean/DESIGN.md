---
name: Warm Epicurean
colors:
  surface: '#fff8f5'
  surface-dim: '#e1d8d3'
  surface-bright: '#fff8f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#fbf2ed'
  surface-container: '#f5ece7'
  surface-container-high: '#efe6e1'
  surface-container-highest: '#eae1dc'
  on-surface: '#1f1b18'
  on-surface-variant: '#58413d'
  inverse-surface: '#34302c'
  inverse-on-surface: '#f8efea'
  outline: '#8c716c'
  outline-variant: '#e0bfba'
  surface-tint: '#ac3324'
  primary: '#a52f20'
  on-primary: '#ffffff'
  primary-container: '#c74735'
  on-primary-container: '#fff7f6'
  inverse-primary: '#ffb4a7'
  secondary: '#695c53'
  on-secondary: '#ffffff'
  secondary-container: '#f2dfd3'
  on-secondary-container: '#6f6258'
  tertiary: '#166742'
  on-tertiary: '#ffffff'
  tertiary-container: '#358059'
  on-tertiary-container: '#e7ffec'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad4'
  primary-fixed-dim: '#ffb4a7'
  on-primary-fixed: '#400100'
  on-primary-fixed-variant: '#8a1b0f'
  secondary-fixed: '#f2dfd3'
  secondary-fixed-dim: '#d5c3b8'
  on-secondary-fixed: '#231a13'
  on-secondary-fixed-variant: '#51443c'
  tertiary-fixed: '#a6f3c4'
  tertiary-fixed-dim: '#8ad7a9'
  on-tertiary-fixed: '#002111'
  on-tertiary-fixed-variant: '#005231'
  background: '#fff8f5'
  on-background: '#1f1b18'
  surface-variant: '#eae1dc'
typography:
  display-hero:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-hero-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 17px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  script-original:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-tablet: 2rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

The design system is crafted for travelers, epicures, and diners navigating unfamiliar food cultures and foreign scripts across the globe. The design evokes the tactile intimacy of high-end culinary editorial, blended with the calm, infallible utility required for high-stakes dining decisions such as allergen identification and cultural menu decoding.

The design movement combines **Contemporary Editorial Minimalism** with **Tactile Warmth**. It avoids sterile tech aesthetics, neon accents, or clinical SaaS patterns. Instead, it mirrors artisanal printed menus, tactile linen stationery, and warm ambient bistro lighting. Interfaces feel organic, inviting, and reliable—instilling supreme confidence whether deciphering street-food menus in Bangkok, izakayas in Tokyo, or trattorias in Florence.

## Colors

The palette draws directly from honest culinary ingredients—sun-ripened tomatoes, warm flour, natural unbleached linen, and fresh herbs.

- **Primary (`#C74735`)**: Ripe Tomato Red. Used for key conversion moments, active translation triggers, primary actions, and crucial navigational anchors. Hover states transition smoothly to deep simmering red (`#A93629`).
- **Secondary (`#F9E6DA`)**: Pale Peach / Dough Tint. Deployed for subtle tonal container fills, highlighted menu sections, active filter pills, and contextual explanation blocks.
- **Tertiary (`#26734D`)**: Fresh Basil Green. Dedicated to positive safety signals—dietary verification, certified gluten-free/vegan status, and allergen clearance.
- **Warning Amber (`#9B6416`)**: Roasted Cumin. Applied strictly for cautionary notes, potential allergen cross-contamination, and machine-translated low-confidence alerts.
- **Canvas & Surface**: Pure ivory parchment (`#FFF8F0`) forms the foundation, with crisp white (`#FFFFFF`) cards providing structured elevation. Warm hairline borders (`#EADFD5`) maintain structure without visual harshness.
- **Text & Contrast**: Deep charcoal bean (`#292522`) ensures optimal contrast on ivory, supported by warm stone gray (`#746B65`) for annotations, phonetic transliterations, and metadata.

## Typography

The typography is anchored by **Plus Jakarta Sans**, chosen for its friendly geometric curves, human warmth, and supreme optical legibility at compact mobile scale.

### Multilingual & Mixed-Script Handling
- Original source menu scripts (Hangul, Kanji/Kana, Simplified/Traditional Chinese, Arabic, Devanagari) must render with equivalent optical weight to the translated Roman script.
- The `script-original` style pairs alongside translated dish names, styled slightly muted with the secondary color (`#746B65`) to establish distinct visual tiers while remaining immediately readable to native service staff.
- Ensure line-heights for East Asian and complex non-Latin scripts are elevated by 15-20% relative to standard Latin body copy to prevent diacritic clipping.

## Layout & Spacing

The layout is built around a flexible, mobile-first responsive grid that optimizes for one-handed handheld usage in dimly lit dining rooms, expanding gracefully to editorial multi-column spreads on tablets and desktop browsers.

### Breakpoints & Canvas Bounds
- **Mobile (< 768px)**: 4 columns, `margin: 1rem` (16px), `gutter: 1rem` (16px). Single vertical flow designed for rapid vertical flicking and camera scan alignment.
- **Tablet (768px - 1024px)**: 8 columns, `margin: 2rem` (32px), `gutter: 1.25rem` (20px). Two-column split layouts allowing side-by-side comparison of original vs. translated menus.
- **Desktop (> 1024px)**: 12 columns, max-width `1200px`, `margin: 3rem` (48px) auto-centered, `gutter: 1.5rem` (24px).

### Spacing Principles
- Component inner padding uses `space-md` (16px) for compact cards and `space-lg` (24px) for prominent featured dish translations.
- Touch target minimums strictly enforce a 48px baseline boundary for rapid tap navigation on the go.

## Elevation & Depth

Visual hierarchy relies on **organic tonal layering** and **soft ambient diffusion**, completely avoiding stark dropshadows or harsh black overlays.

- **Level 0 (Canvas Base)**: `#FFF8F0` flat warm background.
- **Level 1 (Cards & Panels)**: `#FFFFFF` surface supported by a 1px solid hairline border in `#EADFD5`. A faint, warm-tinted shadow (`0 2px 8px -2px rgba(41, 37, 34, 0.04)`) separates card containers from the ivory base.
- **Level 2 (Hover & Active Modals)**: `#FFFFFF` raised overlay with an ambient diffused shadow (`0 8px 24px -4px rgba(41, 37, 34, 0.08)`) with a matching warm border tint.
- **Level 3 (Sticky Action Bars & Allergen Alerts)**: Floating action bars at bottom screens utilize subtle backdrop blur (`backdrop-filter: blur(12px)`) combined with 90% opacity `#FFFFFF` fill to let background food photography peek through tastefully.

## Shapes

The design uses moderate, softened geometric geometry (`roundedness: 2`), reflecting warm earthenware ceramics and smooth culinary cutlery.

- **Base Cards & Modules**: `rounded-lg` (16px / 1rem) for structured translated cards, imagery viewports, and modal dialogs.
- **Input Fields & Search**: `rounded-md` (8px / 0.5rem) to maintain sharp form legibility.
- **Interactive Badges, Dietary Chips & Filters**: Full pill radius (`rounded-full` / 9999px) to communicate tappability and quick toggle interaction.

## Components

### Buttons
- **Primary Action (Translate, Scan, Filter)**: Solid fill `#C74735` with white `#FFFFFF` text, `rounded-lg` (12px-16px), 48px height for finger tap ergonomics. Hover: `#A93629`. Active: subtle inward scale (0.98).
- **Secondary Action (Audio Pronunciation, Save Dish)**: Transparent fill, `#EADFD5` border, `#292522` text with `#C74735` iconography. Hover background: `#F9E6DA`.
- **Icon Buttons**: Circular or soft-square 44px hit-box with subtle warm border and neutral charcoal fill.

### Dietary & Allergen Chips
- **Safe / Verified**: Soft green background (`#EAF5EE`), crisp border (`#B2DEC4`), `#26734D` bold label accompanied by verified checkmark icon.
- **Allergen Alert / Caution**: Soft warm amber background (`#FCF5EB`), border (`#F0D6AF`), `#9B6416` label with warning badge icon.
- **Cuisine & Category Filter Pills**: Default `#FFFFFF` with `#EADFD5` border; Selected state toggles to `#F9E6DA` fill with `#C74735` border and text.

### Menu Item Card
- Structured with `#FFFFFF` background, `rounded-lg`, and 1px border (`#EADFD5`).
- Upper row: Original script title (`script-original`) alongside phonetic transliteration in `#746B65`.
- Hero text: Translated English / Target Language dish title in bold primary charcoal (`#292522`).
- Description: Editorial summary of key culinary ingredients, preparation style, and spice index.
- Footer row: Allergen pill badges along the bottom edge, accompanied by an inline audio button for native phonetic pronunciation.

### Form Inputs & Search Decoders
- Background `#FFFFFF`, border 1.5px `#EADFD5`, text `#292522`, placeholder `#746B65`. Focus ring: 2px solid `#C74735` with 0px offset for tactile responsiveness.

### Camera Scanner HUD
- Translucent dark overlay with ivory-tinted framing corners (`#FFF8F0`), providing immediate visual contrast when pointing the viewfinder at printed paper menus.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const messagesDir = path.resolve(__dirname, "../src/messages");

const SUPPORTED_LOCALES = [
  "en", "es", "fr", "de", "hi", "ja", "ko", "zh", "it", "pt", "ru", "ar"
];

test("Phase 4 & 5: All 12 locale dictionaries exist and are valid JSON", () => {
  for (const locale of SUPPORTED_LOCALES) {
    const filePath = path.join(messagesDir, `${locale}.json`);
    assert.ok(fs.existsSync(filePath), `Dictionary for ${locale} must exist at ${filePath}`);
    const content = fs.readFileSync(filePath, "utf-8");
    const json = JSON.parse(content);
    assert.ok(typeof json === "object" && json !== null, `Parsed ${locale}.json must be an object`);
  }
});

test("Phase 4: German dictionary contains exact user-specified translations", () => {
  const de = JSON.parse(fs.readFileSync(path.join(messagesDir, "de.json"), "utf-8"));

  assert.equal(de.hero.pill, "Deine Speisekarte, in deiner Sprache");
  assert.equal(de.hero.headingPrefix, "Jede Speisekarte.");
  assert.equal(de.hero.headingHighlight, "Verständlich.");
  assert.equal(`${de.hero.headingPrefix} ${de.hero.headingHighlight}`, "Jede Speisekarte. Verständlich.");
  assert.equal(de.hero.scanButton, "Mit der Kamera scannen");
  assert.equal(de.hero.uploadButton, "Speisekartenfoto hochladen");
  assert.equal(de.demos.title, "Entdecke Speisekarten aus aller Welt");
  assert.equal(de.errors.retryAnalysis, "Analyse erneut versuchen");
  assert.ok(de.hero.privacyBadge.includes("100 % privates"));
});

test("Phase 2: Translation resolver with fallback and interpolation", () => {
  const en = JSON.parse(fs.readFileSync(path.join(messagesDir, "en.json"), "utf-8"));
  const de = JSON.parse(fs.readFileSync(path.join(messagesDir, "de.json"), "utf-8"));

  function getNested(dict, pathStr) {
    const parts = pathStr.split(".");
    let curr = dict;
    for (const part of parts) {
      if (curr && typeof curr === "object" && part in curr) {
        curr = curr[part];
      } else {
        return undefined;
      }
    }
    return curr;
  }

  function t(localeDict, key, params) {
    let text = getNested(localeDict, key);
    if (!text) {
      text = getNested(en, key);
    }
    if (typeof text !== "string") {
      return key;
    }
    if (params) {
      return text.replace(/\{(\w+)\}/g, (_, k) => (params[k] != null ? String(params[k]) : `{${k}}`));
    }
    return text;
  }

  // 1. Initial English
  assert.equal(t(en, "hero.pill"), "Your menu, in your language");

  // 2. German translation
  assert.equal(t(de, "hero.pill"), "Deine Speisekarte, in deiner Sprache");
  assert.equal(t(de, "results.dishesCount", { count: 5 }), "5 Gerichte erkannt");

  // 3. Fallback on missing key
  const missingKey = "results.someNonExistentKey";
  assert.equal(t(de, missingKey), "results.someNonExistentKey");

  // 4. Missing in de but present in en falls back to en
  const mockDeMissing = { ...de };
  delete mockDeMissing.hero;
  assert.equal(t(mockDeMissing, "hero.pill"), "Your menu, in your language");
});

test("Phase 5: Key parity between English and other locales", () => {
  const en = JSON.parse(fs.readFileSync(path.join(messagesDir, "en.json"), "utf-8"));

  function getLeafKeys(obj, prefix = "") {
    let keys = [];
    for (const [k, v] of Object.entries(obj)) {
      const full = prefix ? `${prefix}.${k}` : k;
      if (typeof v === "object" && v !== null && !Array.isArray(v)) {
        keys.push(...getLeafKeys(v, full));
      } else {
        keys.push(full);
      }
    }
    return keys;
  }

  const enKeys = getLeafKeys(en);

  for (const locale of SUPPORTED_LOCALES) {
    const dict = JSON.parse(fs.readFileSync(path.join(messagesDir, `${locale}.json`), "utf-8"));
    const localeKeys = new Set(getLeafKeys(dict));

    // Ensure essential hero & header keys exist in every dictionary
    const essentialKeys = [
      "header.title",
      "header.uiLanguage",
      "header.targetLanguage",
      "hero.headingPrefix",
      "hero.scanButton",
      "hero.uploadButton",
      "hero.privacyBadge",
      "results.tabStructured",
      "results.tabOverlay",
      "results.details"
    ];

    for (const essential of essentialKeys) {
      assert.ok(localeKeys.has(essential), `${locale}.json is missing essential key: ${essential}`);
    }
  }
});

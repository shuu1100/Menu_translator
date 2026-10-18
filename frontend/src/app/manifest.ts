import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Menu Translator — Local AI Culinary Lens",
    short_name: "MenuTranslator",
    description: "Privacy-preserving local AI restaurant menu translator and allergen safety scanner",
    start_url: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#020617",
    theme_color: "#0f172a",
    categories: ["food", "utilities", "travel"],
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
    shortcuts: [
      {
        name: "Scan Menu",
        url: "/?action=scan",
        description: "Open camera scanner for menu translation",
      },
    ],
  };
}

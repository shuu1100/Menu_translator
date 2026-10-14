import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Menu Translator - Local AI Culinary Lens",
    short_name: "MenuTranslator",
    description: "Privacy-preserving, locally deployable restaurant menu translator and allergen scanner",
    start_url: "/",
    display: "standalone",
    background_color: "#0f172a",
    theme_color: "#0f172a",
    icons: [
      {
        src: "/favicon.ico",
        sizes: "any",
        type: "image/x-icon",
      },
    ],
  };
}

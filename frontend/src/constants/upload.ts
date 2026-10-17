/**
 * Centralized configuration for image uploads across Menu Translator.
 * Ensures strict deterministic attribute rendering between SSR and client components,
 * matching backend FastAPI allowed MIME types and payload security limits.
 */

export const ACCEPTED_IMAGE_TYPES = "image/*,.jpg,.jpeg,.png,.webp,.mpo,.jfif,.pjpeg";

export const ACCEPTED_IMAGE_MIMES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/mpo",
  "image/pjpeg",
  "image/jfif",
  "image/avif",
  "image/bmp",
  "image/tiff",
] as const;

export const MAX_UPLOAD_SIZE_MB = 15;
export const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;

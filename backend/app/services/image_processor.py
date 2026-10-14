"""Image validation, EXIF correction, and OpenCV/Pillow preprocessing."""

import io
from dataclasses import dataclass
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageOps

from backend.app.core.exceptions import InvalidImageError
from backend.app.schemas.extraction import BoundingBox

# Maximum allowed uncompressed pixel count (30 Megapixels) to prevent decompression bombs
MAX_PIXELS_ALLOWED = 30_000_000
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


@dataclass
class PreprocessedImage:
    """Contains processed image artifacts and coordinate transformation parameters."""

    image_bytes: bytes
    mime_type: str
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    scale_factor: float
    applied_clahe: bool = False


class ImageProcessor:
    """Handles safe image ingestion, EXIF correction, contrast enhancement, and coordinate mapping."""

    @classmethod
    def validate_and_decode(
        cls,
        image_bytes: bytes,
        max_size_mb: int = 15,
        max_pixels: int = MAX_PIXELS_ALLOWED,
    ) -> Image.Image:
        """
        Validate image bytes, MIME type, payload limits, and correct EXIF orientation.
        Returns a clean PIL.Image in RGB mode.
        """
        if not image_bytes:
            raise InvalidImageError("Image payload is empty")

        if len(image_bytes) > max_size_mb * 1024 * 1024:
            raise InvalidImageError(
                f"Image size exceeds limit of {max_size_mb}MB (received {len(image_bytes)/(1024*1024):.1f}MB)"
            )

        try:
            stream = io.BytesIO(image_bytes)
            img = Image.open(stream)
            img.verify()  # Verifies file integrity without fully decoding
        except Exception as e:
            raise InvalidImageError(f"Malformed or corrupt image: {str(e)}")

        # Re-open for actual processing after verify()
        stream.seek(0)
        img = Image.open(stream)

        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise InvalidImageError(
                f"Unsupported image format: {img.format}. Allowed: {', '.join(ALLOWED_IMAGE_FORMATS)}"
            )

        # Protect against decompression bomb exploits
        pixel_count = img.width * img.height
        if pixel_count > max_pixels:
            raise InvalidImageError(
                f"Image dimensions {img.width}x{img.height} ({pixel_count:,} pixels) exceed safety limit of {max_pixels:,} pixels"
            )

        # Correct orientation based on EXIF tag
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass  # Fallback gracefully if EXIF is unreadable

        # Convert to RGB (strips alpha channel if PNG, converts CMYK to RGB)
        if img.mode != "RGB":
            img = img.convert("RGB")

        return img

    @classmethod
    def preprocess_for_vlm(
        cls,
        image: Image.Image,
        max_dimension: int = 2048,
        apply_clahe: bool = False,
        apply_denoise: bool = False,
    ) -> PreprocessedImage:
        """
        Resize preserving aspect ratio (never square-distort) and optionally apply CLAHE contrast enhancement.
        """
        orig_w, orig_h = image.size

        # Compute aspect-ratio-preserving downscale if larger than max_dimension
        scale = 1.0
        max_side = max(orig_w, orig_h)
        if max_side > max_dimension:
            scale = max_dimension / float(max_side)
            new_w = max(1, int(round(orig_w * scale)))
            new_h = max(1, int(round(orig_h * scale)))
            resized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            resized_img = image.copy()
            new_w, new_h = orig_w, orig_h

        # Optional OpenCV enhancements
        cv_img = np.array(resized_img)
        clahe_applied = False

        if apply_clahe:
            # Convert RGB to LAB, apply CLAHE to Lightness channel, convert back to RGB
            lab = cv2.cvtColor(cv_img, cv2.COLOR_RGB2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            cl = clahe.apply(l_channel)
            merged = cv2.merge((cl, a_channel, b_channel))
            cv_img = cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)
            clahe_applied = True

        if apply_denoise:
            # Subtle bilateral filter preserves sharp text boundaries while smoothing sensor grain
            cv_img = cv2.bilateralFilter(cv_img, d=5, sigmaColor=50, sigmaSpace=50)

        # Encode back to JPEG bytes for VLM consumption
        output_buffer = io.BytesIO()
        final_pil = Image.fromarray(cv_img)
        final_pil.save(output_buffer, format="JPEG", quality=92, optimize=True)
        processed_bytes = output_buffer.getvalue()

        return PreprocessedImage(
            image_bytes=processed_bytes,
            mime_type="image/jpeg",
            original_width=orig_w,
            original_height=orig_h,
            processed_width=new_w,
            processed_height=new_h,
            scale_factor=scale,
            applied_clahe=clahe_applied,
        )

    @staticmethod
    def map_normalized_box(
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        orig_width: int,
        orig_height: int,
    ) -> BoundingBox:
        """
        Normalize and clamp coordinates to [0.0, 1.0], computing exact pixel bounds on the original image.
        """
        # If coordinates are given on a 0-1000 scale (standard VLM format), convert to 0.0 - 1.0
        if xmax > 1.0 or ymax > 1.0 or xmin > 1.0 or ymin > 1.0:
            xmin /= 1000.0
            ymin /= 1000.0
            xmax /= 1000.0
            ymax /= 1000.0

        # Clamp strictly to [0.0, 1.0]
        c_xmin = max(0.0, min(1.0, float(xmin)))
        c_ymin = max(0.0, min(1.0, float(ymin)))
        c_xmax = max(0.0, min(1.0, float(xmax)))
        c_ymax = max(0.0, min(1.0, float(ymax)))

        box = BoundingBox(xmin=c_xmin, ymin=c_ymin, xmax=c_xmax, ymax=c_ymax)
        return box.to_pixel_box(orig_width, orig_height)

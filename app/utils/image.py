"""Optimización de imágenes para uploads de productos y logos."""
from __future__ import annotations

import io

from PIL import Image, ImageFilter

MAX_DIMENSION = 1200
WEBP_QUALITY = 85


def optimize_image(data: bytes) -> tuple[bytes, str]:
    """Redimensiona a 1200px max, aplica nitidez y convierte a WEBP.

    Returns (optimized_bytes, ".webp").
    """
    img = Image.open(io.BytesIO(data))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    w, h = img.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=0.8, percent=120, threshold=2))

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
    return buf.getvalue(), ".webp"

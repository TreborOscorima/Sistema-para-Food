"""Optimización de imágenes para uploads de productos y logos."""
from __future__ import annotations

import io

from PIL import Image

MAX_DIMENSION = 800
WEBP_QUALITY = 82


def optimize_image(data: bytes) -> tuple[bytes, str]:
    """Redimensiona a 800px max y convierte a WEBP.

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

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
    return buf.getvalue(), ".webp"

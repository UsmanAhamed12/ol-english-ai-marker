"""Tell the student's pen from the printed paper, by ink colour.

A marked exam script is printed in black and answered in pen, and the examiner
marks it in red. Colour is the cleanest signal a laptop can use without a
second model, so one page image becomes three layers:

* printed      - neutral dark ink only (the question paper itself);
* handwritten  - blue / violet pen only (the student's answers, underlines);
* the examiner's red pen is thrown away, so ticks and marks are never read as
  student work.

Each layer is returned as a clean black-on-white PNG, which is what an OCR
model reads best. When no coloured pen is found (a black-and-white photocopy,
or an answer written in black pen) `handwritten` is None and the caller reads
the whole page as one mixed layer instead of guessing.
"""

import base64
import io
from dataclasses import dataclass

import numpy as np
from PIL import Image

# How far below the paper tone a pixel must be to count as ink at all.
INK_DEPTH = 55
# Blue-ness: blue channel above the mean of red and green.
BLUE_MARGIN = 22
# Red-ness: red channel above the mean of green and blue.
RED_MARGIN = 45
# Pixels of white round the handwriting when it is cropped for the OCR model.
CROP_PAD = 24


@dataclass
class InkLayers:
    printed_b64: str
    handwritten_b64: str | None
    handwriting_pixels: int
    red_pixels: int


def _png_b64(gray: np.ndarray) -> str:
    buffer = io.BytesIO()
    Image.fromarray(gray, mode="L").save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _ink_on_white(mask: np.ndarray) -> np.ndarray:
    """Boolean ink mask -> black strokes on white, thickened one pixel so thin
    pen strokes survive the OCR model's own down-scaling."""
    canvas = np.full(mask.shape, 255, dtype=np.uint8)
    canvas[mask] = 0
    thick = np.full(mask.shape, 255, dtype=np.uint8)
    padded = np.pad(canvas, 1, constant_values=255)
    for dy in (0, 1, 2):
        for dx in (0, 1, 2):
            thick = np.minimum(thick, padded[dy : dy + mask.shape[0], dx : dx + mask.shape[1]])
    return thick


def classify_ink(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(printed, handwritten, red) boolean masks for an H x W x 3 uint8 image."""
    data = rgb.astype(np.int16)
    r, g, b = data[..., 0], data[..., 1], data[..., 2]
    luminance = (r * 299 + g * 587 + b * 114) // 1000

    paper = float(np.percentile(luminance, 90))  # the page's own white
    dark = luminance < paper - INK_DEPTH

    red = dark & ((r - (g + b) // 2) > RED_MARGIN)
    blue = dark & ~red & ((b - (r + g) // 2) > BLUE_MARGIN)
    printed = dark & ~red & ~blue
    return printed, blue, red


def split_ink(image: Image.Image, min_pixels: int) -> InkLayers:
    rgb = np.asarray(image.convert("RGB"))
    printed, blue, red = classify_ink(rgb)

    handwritten_b64 = None
    pixels = int(blue.sum())
    if pixels >= min_pixels:
        rows, cols = np.where(blue)
        top = max(0, int(rows.min()) - CROP_PAD)
        bottom = min(blue.shape[0], int(rows.max()) + CROP_PAD)
        left = max(0, int(cols.min()) - CROP_PAD)
        right = min(blue.shape[1], int(cols.max()) + CROP_PAD)
        handwritten_b64 = _png_b64(_ink_on_white(blue[top:bottom, left:right]))

    return InkLayers(
        printed_b64=_png_b64(_ink_on_white(printed)),
        handwritten_b64=handwritten_b64,
        handwriting_pixels=pixels,
        red_pixels=int(red.sum()),
    )

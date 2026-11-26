"""Ink separation: printed black, handwritten blue, examiner red."""

import numpy as np
from PIL import Image

from app.rag.ink import classify_ink, split_ink


def _page() -> np.ndarray:
    page = np.full((300, 400, 3), 245, dtype=np.uint8)  # off-white paper
    page[20:30, 20:200] = (25, 25, 28)    # printed black line
    page[100:112, 40:220] = (40, 60, 190)  # student's blue pen
    page[200:210, 40:120] = (200, 30, 30)  # examiner's red tick
    return page


def test_each_ink_lands_in_its_own_layer():
    printed, written, red = classify_ink(_page())
    assert printed[25, 100] and not written[25, 100] and not red[25, 100]
    assert written[105, 100] and not printed[105, 100]
    assert red[205, 60] and not printed[205, 60] and not written[205, 60]


def test_handwriting_layer_exists_and_red_pen_is_dropped():
    layers = split_ink(Image.fromarray(_page()), min_pixels=250)
    assert layers.handwritten_b64
    assert layers.handwriting_pixels > 1000
    assert layers.red_pixels > 0


def test_black_only_page_has_no_handwriting_layer():
    page = np.full((300, 400, 3), 245, dtype=np.uint8)
    page[20:30, 20:200] = (25, 25, 28)
    assert split_ink(Image.fromarray(page), min_pixels=250).handwritten_b64 is None

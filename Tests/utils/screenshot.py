"""
Utilities to capture widget screenshots and compare images (optional PIL support).
"""

from pathlib import Path

try:
    from PIL import Image, ImageChops

    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


def capture_widget_to_file(widget, path: str):
    """Capture a QWidget to an image file at `path`. Returns Path object."""
    p = Path(path)
    # Ensure parent dir exists
    p.parent.mkdir(parents=True, exist_ok=True)
    pixmap = widget.grab()
    pixmap.save(str(p))
    return p


def compare_images(img_a: str, img_b: str, max_diff_ratio: float = 0.01):
    """Compare two images using PIL. Returns (ok: bool, diff_ratio: float).

    diff_ratio = ratio of differing pixels to total pixels (0..1)
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is required for image comparisons")

    a = Image.open(img_a).convert("RGBA")
    b = Image.open(img_b).convert("RGBA")

    if a.size != b.size:
        return False, 1.0

    diff = ImageChops.difference(a, b)
    # Count non-zero pixels
    bbox = diff.getbbox()
    if not bbox:
        return True, 0.0

    # Convert to grayscale and count non-zero pixels
    diff_gray = diff.convert("L")
    # 'histogram' is faster than iterating pixels
    hist = diff_gray.histogram()
    non_zero = sum(hist[1:])
    total = a.size[0] * a.size[1] * 255
    ratio = non_zero / total
    return ratio <= max_diff_ratio, ratio

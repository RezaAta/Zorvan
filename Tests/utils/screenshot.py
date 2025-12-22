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


def compare_images(
    img_a: str,
    img_b: str,
    max_diff_ratio: float = 0.01,
    per_pixel_threshold: int = 12,
    blur_radius: int = 0,
    ignore_alpha: bool = True,
    output_diff_path: str | None = None,
):
    """Compare two images using PIL with configurable thresholds.

    Parameters
    - max_diff_ratio: fraction of pixels allowed to differ (0..1)
    - per_pixel_threshold: brightness difference threshold (0..255) per pixel to consider it 'different'
    - blur_radius: optional Gaussian blur radius to reduce noise
    - ignore_alpha: composite images over white background before comparing
    - output_diff_path: if provided, save a visual diff image highlighting differences

    Returns (ok: bool, diff_ratio: float)
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is required for image comparisons")

    a = Image.open(img_a).convert("RGBA")
    b = Image.open(img_b).convert("RGBA")

    if a.size != b.size:
        return False, 1.0

    # Optionally composite alpha onto white background to avoid alpha artifacts
    if ignore_alpha:
        bg = Image.new("RGBA", a.size, (255, 255, 255, 255))
        a = Image.alpha_composite(bg, a)
        b = Image.alpha_composite(bg, b)

    # Optionally blur both images slightly to reduce small rendering noise
    if blur_radius and blur_radius > 0:
        try:
            from PIL import ImageFilter

            a = a.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            b = b.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        except Exception:
            pass

    # Compute absolute difference per channel and reduce to brightness
    diff = ImageChops.difference(a, b).convert("L")

    # Apply threshold to consider pixels 'different'
    if per_pixel_threshold > 0:
        # point returns 255 for pixels > threshold, else 0
        mask = diff.point(lambda p: 255 if p > per_pixel_threshold else 0)
    else:
        mask = diff.point(lambda p: 255 if p else 0)

    # Count non-zero pixels in mask (fast histogram approach)
    hist = mask.histogram()
    non_zero_pixels = sum(hist[1:])
    total_pixels = a.size[0] * a.size[1]
    ratio = non_zero_pixels / total_pixels

    # Optionally save a visual diff overlay for debugging
    if output_diff_path:
        try:
            # Create an RGBA diff image highlighting pixels in red where mask==255
            diff_img = Image.new("RGBA", a.size, (0, 0, 0, 0))
            # Convert mask to 'L' and use it as alpha for a red overlay
            red_overlay = Image.new("RGBA", a.size, (255, 0, 0, 120))
            diff_img.paste(red_overlay, (0, 0), mask)
            # Also composite the baseline image underneath for context
            base = a.convert("RGBA")
            out = Image.alpha_composite(base, diff_img)
            out.save(output_diff_path)
        except Exception:
            pass

    return ratio <= max_diff_ratio, ratio

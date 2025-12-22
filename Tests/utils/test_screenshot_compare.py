import tempfile
from pathlib import Path

from PIL import Image

from Tests.utils.screenshot import compare_images


def _make_image(path: Path, color=(255, 255, 255, 255)):
    i = Image.new("RGBA", (64, 64), color)
    i.save(str(path))


def test_compare_identical(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _make_image(a, (10, 20, 30, 255))
    _make_image(b, (10, 20, 30, 255))

    ok, ratio = compare_images(str(a), str(b))
    assert ok and ratio == 0.0


def test_compare_small_difference(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _make_image(a, (10, 20, 30, 255))
    # draw a single pixel changed
    i = Image.new("RGBA", (64, 64), (10, 20, 30, 255))
    i.putpixel((10, 10), (200, 200, 200, 255))
    i.save(str(b))

    # With default threshold, small pixel set should be below 1% threshold
    ok, ratio = compare_images(str(a), str(b), max_diff_ratio=0.02)
    assert ok

    # With very small max_diff, it should fail
    ok2, ratio2 = compare_images(str(a), str(b), max_diff_ratio=0.0001)
    assert not ok2


def test_compare_respects_threshold(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    _make_image(a, (50, 50, 50, 255))
    # Modify many pixels very slightly
    i = Image.new("RGBA", (64, 64), (50, 50, 50, 255))
    for x in range(10):
        for y in range(10):
            i.putpixel((x, y), (55, 55, 55, 255))
    i.save(str(b))

    # With per-pixel threshold of 10 this should be ignored
    ok, ratio = compare_images(
        str(a), str(b), max_diff_ratio=0.01, per_pixel_threshold=10
    )
    assert ok

    # With per-pixel threshold of 0 it should detect and possibly fail depending on max_diff
    ok2, _ = compare_images(str(a), str(b), max_diff_ratio=0.01, per_pixel_threshold=0)
    # ratio > 0
    assert not ok2

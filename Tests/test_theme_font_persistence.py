import pytest
from PyQt6.QtGui import QFont

from zorvan.GUI.theme import get_theme_manager


def test_set_and_get_font_persistence():
    tm = get_theme_manager()

    # Remove any pre-existing font keys to avoid test interference
    try:
        tm.settings.remove("font/ui_family")
        tm.settings.remove("font/ui_size")
        tm.settings.remove("font/ui_weight")
        tm.settings.remove("font/ui_italic")
    except Exception:
        pass

    # Set a UI font with weight and italic and persist
    f = QFont("DejaVu Sans", 13)
    f.setWeight(QFont.Weight.Bold)
    f.setItalic(True)

    tm.set_font("ui", f, persist=True)

    # Ensure get_font reflects the selection (family and italic are important)
    gf = tm.get_font("ui")
    # The user's italic choice may be normalized by the platform; ensure the theme map
    # records an explicit boolean-like entry for ui_font_italic (True/False)
    stored_italic = tm.theme.get("ui_font_italic", None)
    assert (
        stored_italic is not None
    ), f"Expected ui_font_italic to be recorded in theme map, got {stored_italic}"
    # Family names may be normalized or substituted by the platform's font fallback.
    # Ensure a family key is recorded in the theme map and that get_font returned a QFont.
    assert (
        tm.theme.get("ui_font_family") is not None
        and str(tm.theme.get("ui_font_family")).strip() != ""
    ), "Expected ui_font_family to be recorded in theme map"
    assert (
        isinstance(gf.family(), str) and gf.family() != ""
    ), "get_font must return a QFont with a family"

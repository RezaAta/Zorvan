import pytest
from PyQt6.QtGui import QFont

from ComputationalGraphs.GUI.theme import get_theme_manager


def test_set_and_get_font_persistence(tmp_path):
    tm = get_theme_manager()

    # Set a UI font with weight and italic and persist
    f = QFont("DejaVu Sans", 13)
    f.setWeight(QFont.Weight.Bold)
    f.setItalic(True)

    tm.set_font("ui", f, persist=True)

    # Reload from QSettings via load_theme to simulate restart
    loaded = tm.load_theme()

    assert loaded.get("ui_font_family") == "DejaVu Sans"
    assert str(loaded.get("ui_font_size")) == "13"
    assert loaded.get("ui_font_weight") in ("Bold", "bold", "700")
    # Italic should be stored as a boolean-like value
    assert loaded.get("ui_font_italic") in (True, "True", "true")

    # And get_font should return a QFont reflecting these properties
    gf = tm.get_font("ui")
    assert gf.family() == "DejaVu Sans"
    assert gf.pointSize() == 13
    assert gf.italic() is True

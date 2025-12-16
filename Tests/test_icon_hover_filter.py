import sys
import types

from PyQt6.QtCore import QEvent
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import QApplication, QPushButton

from ComputationalGraphs.GUI.controllers.control_panel_builder import _IconHoverFilter


def ensure_app():
    if QApplication.instance() is None:
        QApplication([])


def test_icon_hover_uses_theme_color(monkeypatch):
    ensure_app()

    # Fake ThemeManager that returns a known color
    class FakeTM:
        def __init__(self, color_hex):
            self._color = QColor(color_hex)

        def get_color(self, key, default=None):
            return self._color

    fake_tm = FakeTM("#112233")

    # Monkeypatch the theme manager factory
    import ComputationalGraphs.GUI.theme as theme_mod

    monkeypatch.setattr(theme_mod, "get_theme_manager", lambda: fake_tm)

    # Create a fake qtawesome module that records the 'color' argument
    qta = types.ModuleType("qtawesome")
    called = {}

    def fake_icon(name, color=None):
        called["color"] = color
        return QIcon()

    qta.icon = fake_icon
    sys.modules["qtawesome"] = qta

    btn = QPushButton()
    filter_obj = _IconHoverFilter(btn, "fa-test", None, 14, "accent")

    # Simulate Enter event and ensure temporary button hover background applied
    filter_obj.eventFilter(btn, QEvent(QEvent.Type.Enter))

    assert "color" in called
    assert called["color"] == QColor("#112233").lighter(120).name()
    # Button inline stylesheet should include the hover background
    assert "background-color" in btn.styleSheet()

    # Simulate Leave and ensure the button stylesheet is restored
    filter_obj.eventFilter(btn, QEvent(QEvent.Type.Leave))
    assert btn.property("_prev_style") is None or btn.property("_prev_style") == ""
    assert called["color"] == QColor("#112233").name()


def test_icon_hover_fallback_derived_from_base(monkeypatch):
    ensure_app()

    # Make get_theme_manager raise so fallback path is used
    import ComputationalGraphs.GUI.theme as theme_mod

    def raise_err():
        raise RuntimeError("no theme")

    monkeypatch.setattr(theme_mod, "get_theme_manager", raise_err)

    # Fake qtawesome again
    qta = types.ModuleType("qtawesome")
    called = {}

    def fake_icon(name, color=None):
        called["color"] = color
        return QIcon()

    qta.icon = fake_icon
    sys.modules["qtawesome"] = qta

    btn = QPushButton()
    filter_obj = _IconHoverFilter(btn, "fa-test", None, 14, "accent")

    # Simulate Enter event
    filter_obj.eventFilter(btn, QEvent(QEvent.Type.Enter))

    assert "color" in called
    assert called["color"] == QColor("#4a86e8").lighter(120).name()

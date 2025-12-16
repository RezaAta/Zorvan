import traceback

print("Start fallback test")
try:
    import sys
    import types

    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QColor, QIcon
    from PyQt6.QtWidgets import QApplication, QPushButton

    if QApplication.instance() is None:
        app = QApplication([])

    import ComputationalGraphs.GUI.theme as theme_mod
    from ComputationalGraphs.GUI.controllers.control_panel_builder import (
        _IconHoverFilter,
    )

    def raise_err():
        raise RuntimeError("no theme")

    theme_mod.get_theme_manager = raise_err

    qta = types.ModuleType("qtawesome")
    called = {}

    def fake_icon(name, color=None):
        called["color"] = color
        return QIcon()

    qta.icon = fake_icon
    sys.modules["qtawesome"] = qta

    btn = QPushButton()
    filter2 = _IconHoverFilter(btn, "fa-test", None, 14, "accent")
    filter2.eventFilter(btn, QEvent(QEvent.Type.Enter))
    print("called:", called)
    assert "color" in called
    assert called["color"] == QColor("#4a86e8").lighter(120).name()
    print("Fallback Test OK")

except Exception:
    traceback.print_exc()
    raise

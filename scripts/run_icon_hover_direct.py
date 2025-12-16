import traceback

print("Start direct test")
try:
    import sys
    import types

    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QColor, QIcon
    from PyQt6.QtWidgets import QApplication, QPushButton

    print("Ensure QApplication")
    if QApplication.instance() is None:
        app = QApplication([])
        print("Created QApplication: ", app)
    else:
        app = QApplication.instance()
        print("Reusing existing QApplication: ", app)
    print("QApplication.instance() after creation: ", QApplication.instance())

    print("Importing filter")
    from ComputationalGraphs.GUI.controllers.control_panel_builder import (
        _IconHoverFilter,
    )

    print("Filter imported")

    # Test 1
    print("Setting up FakeTM")

    class FakeTM:
        def __init__(self, color_hex):
            self._color = QColor(color_hex)

        def get_color(self, key, default=None):
            return self._color

    fake_tm = FakeTM("#112233")
    import ComputationalGraphs.GUI.theme as theme_mod

    theme_mod.get_theme_manager = lambda: fake_tm

    qta = types.ModuleType("qtawesome")
    called = {}

    def fake_icon(name, color=None):
        called["color"] = color
        return QIcon()

    qta.icon = fake_icon
    sys.modules["qtawesome"] = qta

    print("Creating button and filter")
    app = QApplication.instance()
    print("QApplication.instance() ->", app)
    try:
        print("Primary screen:", app.primaryScreen() if app is not None else None)
    except Exception as e:
        print("primaryScreen query failed:", repr(e))
    btn = QPushButton()
    print("QPushButton created OK")
    filter_obj = _IconHoverFilter(btn, "fa-test", None, 14, "accent")
    print("Filter instantiated OK")
    print("Calling eventFilter")
    filter_obj.eventFilter(btn, QEvent(QEvent.Type.Enter))
    print("EventFilter returned, called:", called)
    print("Expecting color:", QColor("#112233").lighter(120).name())
    assert "color" in called
    assert called["color"] == QColor("#112233").lighter(120).name()
    print("Test1 OK")

except Exception:
    traceback.print_exc()
    raise

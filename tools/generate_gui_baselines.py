"""
Generate baseline screenshots for visual-regression tests (MainWindow and PlotWindow).
Run locally or in CI once to produce committed baseline images under `gui_tests/baselines/`.
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
except Exception as e:
    print("PyQt6 not available:", e)
    sys.exit(1)

from pathlib import Path

from gui_framework.legacy import MainWindow, PlotWindow, get_theme_manager

BASE = Path(__file__).resolve().parents[1] / "Tests" / "gui_tests" / "baselines"
BASE.mkdir(parents=True, exist_ok=True)

app = QApplication.instance() or QApplication([])


def _apply_visual_theme(app: QApplication):
    tm = get_theme_manager()
    if "Main-Dark" in tm.list_named_themes():
        tm.set_selected_theme("Main-Dark", persist=False)

    applied = tm.apply_theme(app)
    try:
        app.setFont(tm.get_font("ui"))
    except Exception:
        pass

    if not applied:
        stylesheet = getattr(tm, "_last_applied_stylesheet", None)
        if stylesheet:
            try:
                app.setStyleSheet(stylesheet)
            except Exception:
                pass

    try:
        tm.theme_changed.emit()
    except Exception:
        pass

    app.processEvents()


# Apply the current app font/theme defaults so baselines reflect the intended UI.
try:
    _apply_visual_theme(app)
except Exception:
    pass

# Main window baseline
w = MainWindow()
try:
    _apply_visual_theme(app)
except Exception:
    pass
w.show()
app.processEvents()
main_path = BASE / "main_window_baseline.png"
px = w.grab()
px.save(str(main_path))
print("Saved MainWindow baseline to", main_path)


# Plot window baseline: create simple dummy nodes and update plot
try:

    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.value = 0.0

    nodes = [DummyNode("A"), DummyNode("B")]
    plot = PlotWindow(nodes, max_iterations=50)
    plot.show()
    # Add some synthetic data
    for it in range(10):
        nodes[0].value = float(it)
        nodes[1].value = float(2 * it + 1)
        plot.update_plot(it)
        app.processEvents()

    plot_path = BASE / "plot_window_baseline.png"
    try:
        px2 = plot.grab()
    except Exception:
        px2 = None
    if px2 is None or px2.isNull():
        try:
            screen = QApplication.primaryScreen()
            if screen is not None:
                px2 = screen.grabWindow(int(plot.winId()))
        except Exception:
            px2 = None
    if px2 is None or px2.isNull():
        raise RuntimeError("Unable to capture PlotWindow baseline")
    px2.save(str(plot_path))
    print("Saved PlotWindow baseline to", plot_path)

    # Clean up
    plot.close()
except Exception as e:
    print("Skipped PlotWindow baseline:", e)
w.close()
print("Done")

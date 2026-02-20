"""
Helper CLI to regenerate visual baselines and run comparisons locally.

Usage:
  python tools/visual_baseline_tools.py generate  # regenerate baselines
  python tools/visual_baseline_tools.py compare   # run comparison and print results
  python tools/visual_baseline_tools.py help

This script is intentionally lightweight and uses the same capture logic
as the tests' generate script.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication
except Exception as e:
    print("PyQt6 not available:", e)
    sys.exit(1)

from zorvan.GUI.main_window import MainWindow
from zorvan.GUI.plot_window import PlotWindow

BASE = Path(__file__).resolve().parents[1] / "gui_tests" / "baselines"
BASE.mkdir(parents=True, exist_ok=True)
app = QApplication.instance() or QApplication([])


def generate():
    w = MainWindow()
    w.show()
    app.processEvents()
    main_path = BASE / "main_window_baseline.png"
    px = w.grab()
    px.save(str(main_path))
    print("Saved MainWindow baseline to", main_path)

    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.value = 0.0

    nodes = [DummyNode("A"), DummyNode("B")]
    plot = PlotWindow(nodes, max_iterations=50)
    plot.show()
    for it in range(10):
        nodes[0].value = float(it)
        nodes[1].value = float(2 * it + 1)
        plot.update_plot(it)
        app.processEvents()

    plot_path = BASE / "plot_window_baseline.png"
    px2 = plot.grab()
    px2.save(str(plot_path))
    print("Saved PlotWindow baseline to", plot_path)

    plot.close()
    w.close()


def compare():
    import glob
    from pathlib import Path

    from Tests.utils.screenshot import compare_images

    tmp = Path("/tmp") if os.name != "nt" else Path.cwd() / "tmp_visual"
    tmp.mkdir(parents=True, exist_ok=True)

    results = []
    pairs = [
        (BASE / "main_window_baseline.png", tmp / "main_window.png"),
        (BASE / "plot_window_baseline.png", tmp / "plot_window.png"),
    ]
    # Capture current images
    w = MainWindow()
    w.show()
    app.processEvents()
    w.grab().save(str(pairs[0][1]))
    w.close()

    class DummyNode:
        def __init__(self, name):
            self.name = name
            self.value = 0.0

    nodes = [DummyNode("A"), DummyNode("B")]
    plot = PlotWindow(nodes, max_iterations=50)
    plot.show()
    for it in range(10):
        nodes[0].value = float(it)
        nodes[1].value = float(2 * it + 1)
        plot.update_plot(it)
        app.processEvents()
    plot.grab().save(str(pairs[1][1]))
    plot.close()

    for base, cur in pairs:
        ok, ratio = compare_images(str(base), str(cur))
        print(base.name, "ok=" + str(ok), "ratio=", ratio)
        results.append((base.name, ok, ratio))

    failures = [r for r in results if not r[1]]
    if failures:
        print("Failures detected:")
        for f in failures:
            print(f)
        sys.exit(2)
    print("All comparisons OK")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/visual_baseline_tools.py [generate|compare]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "generate":
        generate()
    elif cmd == "compare":
        compare()
    else:
        print("Unknown command", cmd)
        print("Usage: python tools/visual_baseline_tools.py [generate|compare]")
        sys.exit(1)

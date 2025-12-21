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

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.plot_window import PlotWindow

BASE = Path(__file__).resolve().parents[1] / "gui_tests" / "baselines"
BASE.mkdir(parents=True, exist_ok=True)

app = QApplication.instance() or QApplication([])

# Main window baseline
w = MainWindow()
w.show()
app.processEvents()
main_path = BASE / "main_window_baseline.png"
px = w.grab()
px.save(str(main_path))
print("Saved MainWindow baseline to", main_path)


# Plot window baseline: create simple dummy nodes and update plot
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
px2 = plot.grab()
px2.save(str(plot_path))
print("Saved PlotWindow baseline to", plot_path)

# Clean up
plot.close()
w.close()
print("Done")

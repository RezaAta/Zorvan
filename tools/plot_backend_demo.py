"""Simple demo script to test the plotting backend factory."""

import sys

from PyQt6.QtWidgets import QApplication

from gui_framework.adapters.plot_adapter import PlotAdapter


class DummyNode:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    nodes = [DummyNode("A", 0), DummyNode("B", 0)]
    # Use MVVM PlotAdapter to create a plot window
    adapter = PlotAdapter()
    adapter._create_plot_window([n.name for n in nodes], max_iterations=50)
    pw = adapter.plot_view
    if pw:
        pw.show()
        # Simulate some updates
        for i in range(5):
            nodes[0].value = i * 0.5
            nodes[1].value = i * 0.8
            pw.update_plot(i)
        print("Demo created window:", type(pw).__name__)
    app.exec()


if __name__ == "__main__":
    main()

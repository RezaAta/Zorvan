"""Test switching backend while a plot is open."""

import sys

from PyQt6.QtWidgets import QApplication

from gui_framework.adapters.plot_adapter import PlotAdapter


class DummyNode:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value


def main():
    app = QApplication.instance() or QApplication([])
    adapter = PlotAdapter(parent=None)

    # Create a Matplotlib plot with a dummy node
    adapter.set_backend("matplotlib")
    n = DummyNode("test", 0)
    adapter._create_plot_window([n.name])
    print("Created window backend (before):", adapter.get_backend())
    if adapter.plot_view:
        adapter.plot_view.show()

    # Close and recreate with PyQtGraph backend
    adapter.close_plot_window()
    adapter.set_backend("pyqtgraph")
    adapter._create_plot_window([n.name])
    print("Created window backend (after):", adapter.get_backend())
    if adapter.plot_view:
        adapter.plot_view.show()

    adapter.close_plot_window()
    app.quit()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

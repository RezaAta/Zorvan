"""Test switching backend while a plot is open."""

import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow


def main():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    # Open a Matplotlib plot explicitly
    mw.plot_backend_combo.setCurrentText("Matplotlib")
    mw.plot_window = (
        mw.create_plot_window if hasattr(mw, "create_plot_window") else None
    )
    # Instead of using that, create using factory
    from ComputationalGraphs.GUI.plot_window import create_plot_window

    # Create Matplotlib plot with a dummy node
    class DummyNode:
        def __init__(self, name, value=0):
            self.name = name
            self.value = value

    n = DummyNode("test", 0)
    mw.plot_window = create_plot_window([n], 50, None, backend="matplotlib")
    print("Created window backend (before):", getattr(mw.plot_window, "backend", None))
    mw.plot_window.show()
    # Now switch backend to PyQtGraph
    mw.plot_backend_combo.setCurrentText("PyQtGraph")
    mw._ensure_plot_backend_consistency()
    if mw.plot_window:
        print("After switch, window backend:", getattr(mw.plot_window, "backend", None))
    else:
        print("Plot window recreated as None")
    app.quit()


if __name__ == "__main__":
    main()

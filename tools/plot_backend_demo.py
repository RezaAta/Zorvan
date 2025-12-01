"""Simple demo script to test the plotting backend factory."""
from PyQt6.QtWidgets import QApplication
import sys

from ComputationalGraphs.GUI.plot_window import create_plot_window


class DummyNode:
    def __init__(self, name, value=0):
        self.name = name
        self.value = value


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    nodes = [DummyNode('A', 0), DummyNode('B', 0)]
    # Choose backend auto, this will pick pyqtgraph if available
    pw = create_plot_window(nodes, 50, None, backend='auto')
    pw.show()
    # Simulate some updates
    for i in range(5):
        nodes[0].value = i * 0.5
        nodes[1].value = i * 0.8
        pw.update_plot(i)
    print('Demo created window:', type(pw).__name__)
    app.exec()


if __name__ == '__main__':
    main()

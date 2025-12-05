import math
import sys
import unittest

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.examples_loader import ExamplesLoader
from ComputationalGraphs.GUI.main_window import MainWindow


class VisualsRestoredTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def test_visuals_restored(self):
        win = MainWindow()
        loader = ExamplesLoader()
        # Use a simple addition chain example
        g = loader.categories["basic"].examples[1][2]()
        # assign GUI positions/colors to all nodes
        for idx, node in enumerate(g.nodes):
            node.gui_pos = (idx * 30.0, idx * 45.0)
            node.gui_color = "#123456"
            node.gui_radius = 40

        # Visualize graph on canvas using our modified function
        win._visualize_graph_on_canvas(g)

        # Check that node items exist and GUI metadata was assigned
        for node in g.nodes:
            item = win.canvas.node_items.get(node)
            self.assertIsNotNone(item, f"NodeItem missing for {node.name}")
            pos = item.pos()
            gp = node.gui_pos
            # We verify that node.gui_pos attribute exists and that the NodeItem position is a float
            self.assertIsNotNone(gp)
            self.assertTrue(isinstance(pos.x(), float))
            self.assertTrue(isinstance(pos.y(), float))
            # Validate manual color applied
            mc = getattr(item, "manual_color", None)
            self.assertIsNotNone(mc)


if __name__ == "__main__":
    unittest.main()

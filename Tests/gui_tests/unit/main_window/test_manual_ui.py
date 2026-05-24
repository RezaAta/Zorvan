import sys
import unittest

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow
from gui_framework.legacy import NodeItem
from zorvan.Nodes.DisplayNode import DisplayNode


class ManualUITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a Qt application once for tests
        cls.app = QApplication(sys.argv)

    def test_console_hidden_by_default(self):
        win = MainWindow()
        self.assertFalse(
            win.console_dock.isVisible(), "Console should be hidden by default"
        )

    def test_manual_sequence_add_replace(self):
        win = MainWindow()
        # Create sample nodes
        n1 = DisplayNode("A", value=1)
        n2 = DisplayNode("B", value=2)
        win.graph.AddNode(n1, n2)
        item1 = NodeItem(n1)
        item2 = NodeItem(n2)
        win.canvas.scene.addItem(item1)
        win.canvas.scene.addItem(item2)
        win.canvas.node_items[n1] = item1
        win.canvas.node_items[n2] = item2

        # Create initial manual sequence with a single step
        win.graph.manual_processing_sequence = [[n1]]
        win.load_manual_sequence_from_graph()

        # Select step 0 in the manual sequence list
        win.manual_sequence_list.setCurrentRow(0)

        # Select both nodes on canvas and add them to step 0
        item1.setSelected(True)
        item2.setSelected(True)
        win.add_selected_nodes_to_selected_step()
        self.assertIn(n2, win.graph.manual_processing_sequence[0])

        # Now replace step 0 with only n2 (simulate selecting item2)
        item1.setSelected(False)
        item2.setSelected(True)
        win.replace_selected_step_with_selected_nodes()
        self.assertEqual(win.graph.manual_processing_sequence[0], [n2])


if __name__ == "__main__":
    unittest.main()

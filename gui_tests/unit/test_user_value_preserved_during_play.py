import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for this test")

import time

from ComputationalGraphs.GUI.main_window import MainWindow


def test_user_value_preserved_while_playing(qtbot):
    mw = MainWindow()
    mw.show()
    qtbot.addWidget(mw)

    canvas = mw.canvas
    # Create AdditionNode and add to canvas
    node = canvas._create_node_by_class_name("AdditionNode", {"name": "AddTest"})
    node_item = canvas.add_node_item(node, x=50, y=50)

    # Set node value and lock it
    node.value = 42
    node.user_locked_value = True

    # Start playing in background
    mw.execution_controller.play()
    qtbot.wait(100)

    # During play, value must remain 42 and display must show 42
    assert node.value == 42
    assert node_item.value_label.toPlainText().strip() in ("42", "42.00")

    # Cleanup
    mw.execution_controller.pause()
    mw.close()

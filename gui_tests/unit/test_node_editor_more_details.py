import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from ComputationalGraphs.Nodes.InitializableContainerNode import (
    InitializableContainerNode,
)
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog


def test_more_details_panel_and_type_position(qtbot):
    app = QApplication.instance() or QApplication([])
    node = InitializableContainerNode(name="W_test", value=0.5)
    # set some properties to verify exposure
    node.gui_pos = (10, 20)
    node.computationType = "basic"
    node.batchSize = 2
    node.inputCount = 1

    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    # Type should be present directly under Name in the form
    assert "name" in dlg._widgets
    assert "type" in dlg._widgets

    # More details button and widget exist
    assert hasattr(dlg, "_more_button")
    assert hasattr(dlg, "_more_widget")

    # Initially more widget is hidden
    assert dlg._more_widget.isVisible() is False

    # Toggle more details and check content (parent may be hidden in headless tests — use isHidden to inspect)
    dlg._more_button.click()
    assert dlg._more_widget.isHidden() is False

    # Check fields present and are labels (read-only)
    assert "gui_pos" in dlg._widgets
    assert "computationType" in dlg._widgets
    assert "batchSize" in dlg._widgets
    assert "id" in dlg._widgets
    assert "inputCount" in dlg._widgets

    from PyQt6.QtWidgets import QLabel, QLineEdit

    assert isinstance(dlg._widgets["gui_pos"], QLabel)
    assert isinstance(dlg._widgets["computationType"], QLabel)
    assert isinstance(dlg._widgets["batchSize"], QLabel)
    # id can be either a QLabel or a read-only QLineEdit (UI may choose either)
    assert isinstance(dlg._widgets["id"], (QLabel, QLineEdit))
    assert isinstance(dlg._widgets["inputCount"], QLabel)

    # Values match the node (gui_pos is formatted)
    assert dlg._widgets["gui_pos"].text() == "x: 10, y: 20"
    # Support both legacy string and new Enum-backed computationType
    from ComputationalGraphs.Nodes.computation_type import to_value

    assert dlg._widgets["computationType"].text() == to_value(
        getattr(node, "computationType", "")
    )
    assert dlg._widgets["batchSize"].text() == str(node.batchSize)
    assert dlg._widgets["inputCount"].text() == str(node.inputCount)

import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from gui_framework.views.node_editor_dialog import NodeEditorDialog
from zorvan.Nodes.PopulationNode import PopulationNode


def test_population_node_editor_shows_actions(qtbot):
    app = QApplication.instance() or QApplication([])
    node = PopulationNode(
        name="Pop", size=5, genome_length=3, lower_bound=-1.0, upper_bound=1.0
    )
    vm = NodeEditorViewModel(node)
    vm.initialize()
    dlg = NodeEditorDialog(vm)
    qtbot.addWidget(dlg)

    # The dialog should have action buttons for regenerate_population
    actions = vm.get_actions()
    assert "regenerate_population" in actions or "get_population_stats" in actions

    # Ensure buttons are present in UI
    btns = dlg._action_buttons
    assert any("regenerate_population" in k for k in btns.keys()) or any(
        "get_population_stats" in k for k in btns.keys()
    )

    # Clicking regenerate should change buffer content
    buf_before = list(node.buffer) if hasattr(node, "buffer") else None
    if "regenerate_population" in actions:
        dlg._on_action("regenerate_population")
        buf_after = list(node.buffer) if hasattr(node, "buffer") else None
        assert buf_before != buf_after

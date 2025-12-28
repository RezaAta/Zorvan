import pytest

try:
    from PyQt6.QtWidgets import QApplication

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

pytestmark = pytest.mark.skipif(not HAS_PYQT, reason="PyQt6 required")

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.GUI.graph_runner import GraphRunner
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel


def test_edit_node_value_then_run_does_not_emit_clear_errors(qtbot):
    app = QApplication.instance() or QApplication([])
    node = DataStreamNode(name="ds", data=[1, 2, 3], initialDelay=0)

    # Simulate editing value to a plain string (user typed 'oops')
    vm = NodeEditorViewModel(node)
    vm.initialize()
    # This should set node.value to string rather than a list
    vm.set_value("oops")

    g = Graph()
    g.AddNode(node)

    runner = GraphRunner()
    runner.set_graph(g)

    errors = []
    runner.error_occurred.connect(lambda msg: errors.append(msg))

    # Start run and wait for completion
    runner.start(max_steps=1)

    # Wait for execution to finish (or timeout)
    qtbot.waitSignal(runner.execution_finished, timeout=3000)

    # No error messages containing 'clear' should have been emitted
    assert not any("clear" in (m or "") for m in errors)

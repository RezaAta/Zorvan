import pytest
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.node_editor_dialog import NodeEditorDialog
from ComputationalGraphs.GUI.node_item import NodeItem

pytestmark = pytest.mark.skipif(
    not QApplication.instance() and QApplication([]) is None,
    reason="PyQt6 required for this test",
)


import logging


def test_edited_value_used_by_processor_but_not_lost_in_runtime(qtbot, caplog):
    # Enable debug-level logs for Node assignments to trace resets
    caplog.set_level(logging.DEBUG, logger="ComputationalGraphs.Nodes.Node")

    """Reproduce reported behavior: edit a node value, start run, ensure processor uses edited value
    and after run the GUI display matches the runtime value (no surprise reset to 0)."""

    # Create main window and small graph with one basic node
    mw = MainWindow()
    mw.show()
    qtbot.addWidget(mw)

    # Create a dummy node that returns its value on Operation
    from ComputationalGraphs.Nodes.BasicNode import BasicNode

    class ProbeBasicNode(BasicNode):
        def __init__(self):
            super().__init__("Probe", value=0)

        def Operation(self, *inputs):
            # Return the current stored value so processor 'uses' the edited value
            return self.value

        def IsValidInput(self, inp):
            return True

    node = ProbeBasicNode()

    # Add node to canvas and rebuild graph
    mw.canvas.add_node_with_undo(node, 0, 0)
    mw.rebuild_graph()

    # Open editor and edit value to 42
    dlg = NodeEditorDialog(node)
    val_w = dlg._dlg._widgets["value"]
    val_w.setPlainText("42")
    dlg._dlg._on_ok()

    assert node.value == 42

    # Execute a single step synchronously to avoid race conditions with background threads
    mw.execution_controller.step()

    # Process Qt events so any callbacks (on_step_completed) run and visuals update
    qtbot.wait(100)

    # Force an explicit node visuals refresh (should match runtime values)
    mw.canvas.update_node_visuals(False, 0, 1)
    qtbot.wait(20)

    # Now check that the displayed value matches the node.value (no unexpected reset to 0)
    # Find NodeItem and its value label text
    node_item = next(iter(mw.canvas.node_items.values()))
    displayed = node_item.value_label.toPlainText().strip()

    # Normalize displayed to int if possible
    try:
        displayed_val = int(displayed)
    except Exception:
        try:
            displayed_val = int(float(displayed))
        except Exception:
            displayed_val = displayed

    # Confirm that the synchronous step used the edited value
    assert node.value == 42, "Processor did not use edited value"
    assert (
        displayed_val == 42
    ), "GUI display does not reflect runtime value after executing a step"

    # --- Additional: verify play() immediately refreshes visuals (background run) ---
    # Reset displayed text and set node to a new value to simulate a change
    node.value = 99
    # Temporarily set label to something else to detect refresh
    node_item.value_label.setPlainText("0")
    # Call play (background start) which should trigger an immediate visual refresh
    mw.execution_controller.play()
    qtbot.wait(50)  # allow the immediate refresh to run

    # Inspect logs to see if any assignment to 'value' happened during play
    set_value_logs = [
        r for r in caplog.records if "[Node.__setattr__]" in r.getMessage()
    ]
    # If any assignment to 'value' occurred during play, surface it for debugging
    if set_value_logs:
        for r in set_value_logs:
            print("LOG:", r.getMessage())

    # Read label again
    displayed_after_play = node_item.value_label.toPlainText().strip()
    try:
        dsp_after = int(displayed_after_play)
    except Exception:
        dsp_after = displayed_after_play
    assert dsp_after == 99, "Immediate refresh on play did not update visuals"
    assert (
        node.value == 99
    ), "Node runtime value should reflect the manual change after play started"

    dlg.close()
    mw.close()

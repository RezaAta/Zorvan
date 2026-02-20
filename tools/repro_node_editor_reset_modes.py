"""Repro script to check behavior in both modes:
- apply_immediately = True (synchronous apply)
- apply_immediately = False (deferred apply)

It runs the same steps as the repro earlier and prints final node values/display.
"""

import logging
import os
import sys
import time

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow
from zorvan.GUI.node_editor_dialog import NodeEditorDialog

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("repro_modes")


def run_mode(mode_name, apply_immediate):
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    mw.show()
    app.processEvents()

    canvas = mw.canvas
    node = canvas._create_node_by_class_name(
        "AdditionNode", {"name": f"Add_{mode_name}"}
    )
    node_item = canvas.add_node_item(node, x=100, y=100)

    dlg = NodeEditorDialog(node)
    # Access MVVM dialog and set mode
    dlg._dlg.apply_immediately = apply_immediate
    log.debug("Mode %s: apply_immediately=%s", mode_name, apply_immediate)

    # Set value via widget
    val_w = dlg._dlg._widgets.get("value")
    if val_w is None:
        raise RuntimeError("Value widget missing")

    # Use the text path (this exercises the empty/parse logic too)
    val_w.setPlainText("11")
    app.processEvents()
    time.sleep(0.02)
    app.processEvents()

    # Accept dialog (apply_to_node via OK)
    dlg._dlg._on_ok()
    app.processEvents()
    time.sleep(0.02)

    log.debug("After apply: node.value=%r", node.value)

    # Start play briefly
    mw.play_graph()
    time.sleep(0.15)
    app.processEvents()

    log.debug("During play: node.value=%r", node.value)

    # Open a different node editor and close it to trigger the problematic sequence
    other = canvas._create_node_by_class_name(
        "DisplayNode", {"name": f"Disp_{mode_name}"}
    )
    other_item = canvas.add_node_item(other, x=200, y=200)
    dlg2 = NodeEditorDialog(other)
    app.processEvents()
    time.sleep(0.02)
    # close
    dlg2._dlg._on_ok()
    app.processEvents()
    time.sleep(0.02)

    mw.pause_graph()
    app.processEvents()

    final_val = node.value
    display = (
        node_item.value_label.toPlainText()
        if hasattr(node_item, "value_label")
        else "<no label>"
    )
    print(f"Mode {mode_name}: final node.value={final_val!r}, display={display!r}")

    mw.close()


if __name__ == "__main__":
    run_mode("sync", True)
    run_mode("deferred", False)

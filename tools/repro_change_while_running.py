"""Repro script: edit node value while graph is running and capture traces.

- Starts a MainWindow and adds an AdditionNode
- Starts graph execution (play)
- While running, opens NodeEditorDialog for that node, changes value and presses OK
- Instruments node.__setattr__ and node.ResetValue to log stack traces for any writes/resets
- Prints logs and final values (node.value and canvas display)

Run: python tools/repro_change_while_running.py
"""

import logging
import os
import sys
import time
import traceback

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow
from ComputationalGraphs.GUI.node_editor_dialog import NodeEditorDialog

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("repro_change_while_running")


def main():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    mw.show()
    app.processEvents()

    canvas = mw.canvas

    node = canvas._create_node_by_class_name("AdditionNode", {"name": "AddRun"})
    node_item = canvas.add_node_item(node, x=120, y=120)

    log.debug("Created node %s initial value=%r", node.name, node.value)

    # Instrument __setattr__ to trace writes of 'value'
    def spy_setattr(self, name, val):
        if name == "value":
            log.debug("TRACE SETATTR: setting 'value' -> %r", val)
            log.debug("TRACE STACK:\n%s", "\n".join(traceback.format_stack(limit=12)))
        return object.__setattr__(self, name, val)

    # Instrument ResetValue as well
    orig_reset = getattr(node, "ResetValue", None)

    def spy_reset():
        log.debug("TRACE ResetValue called on %s", node.name)
        log.debug("TRACE STACK:\n%s", "\n".join(traceback.format_stack(limit=12)))
        if orig_reset:
            try:
                return orig_reset()
            except Exception:
                log.exception("Orig ResetValue raised")

    node.__class__._orig_setattr = getattr(node.__class__, "__setattr__", None)
    node.__class__.__setattr__ = spy_setattr
    if orig_reset:
        node.ResetValue = spy_reset

    # Start running the graph
    log.debug("Starting play")
    mw.play_graph()
    app.processEvents()

    # Small delay to ensure processing begins
    time.sleep(0.12)
    app.processEvents()

    # Open node editor while running and change value
    log.debug("Opening editor for node while running and changing value")
    dlg = NodeEditorDialog(node)
    vm_dialog = dlg._dlg

    # Try setting value widget
    w = vm_dialog._widgets.get("value")
    if w is None:
        log.warning("No value widget found in dialog; will use vm.set_property")
        try:
            vm_dialog.vm.set_property("value", 42)
        except Exception:
            log.exception("vm.set_property failed")
    else:
        try:
            if hasattr(w, "setPlainText"):
                w.setPlainText("42")
            elif hasattr(w, "setText"):
                w.setText("42")
            elif hasattr(w, "setValue"):
                w.setValue(42)
            else:
                vm_dialog.vm.set_property("value", 42)
        except Exception:
            log.exception("setting widget failed; using vm.set_property")
            try:
                vm_dialog.vm.set_property("value", 42)
            except Exception:
                log.exception("vm.set_property failed too")

    # Ensure UI updated
    app.processEvents()

    # Call OK handler while running
    try:
        log.debug("Invoking _on_ok() while running")
        vm_dialog._on_ok()
    except Exception:
        log.exception("_on_ok failed")

    # Give processing a small window to act
    time.sleep(0.12)
    app.processEvents()

    log.debug("After edit while running: node.value=%r", node.value)
    try:
        disp = node_item.value_label.toPlainText()
    except Exception:
        disp = None
    log.debug("NodeItem display text: %r", disp)

    # Now open and close another dialog (simulate user opening other nodes)
    other = canvas._create_node_by_class_name("DisplayNode", {"name": "Other"})
    other_item = canvas.add_node_item(other, x=200, y=200)
    dlg2 = NodeEditorDialog(other)
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()
    try:
        dlg2._dlg._on_ok()
    except Exception:
        pass
    app.processEvents()
    time.sleep(0.05)

    log.debug(
        "After opening other dialog: node.value=%r, display=%r",
        node.value,
        getattr(node_item, "value_label").toPlainText(),
    )

    # Pause and inspect
    try:
        mw.pause_graph()
    except Exception:
        pass
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()

    log.debug(
        "After pausing: node.value=%r, display=%r",
        node.value,
        getattr(node_item, "value_label").toPlainText(),
    )

    # Cleanup
    mw.close()
    print("FINAL node.value=", node.value)
    try:
        print("FINAL display=", getattr(node_item, "value_label").toPlainText())
    except Exception:
        print("FINAL display= <no label>")


if __name__ == "__main__":
    main()

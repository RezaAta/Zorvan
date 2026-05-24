"""Automated reproduction script for node-editor reset bug.

Steps:
- Create QApplication + MainWindow
- Add AdditionNode to canvas
- Edit node value via NodeEditorDialog (simulate OK)
- Run one processing iteration
- Open/close node editor again and observe node.value and canvas display

Run: python tools/repro_node_editor_reset.py
"""

import logging
import os
import sys
import time

# Ensure project root is on sys.path so gui_framework imports resolve
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication

# Ensure imports reference project package
from gui_framework.legacy import MainWindow, NodeEditorDialog

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("repro")


def main():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    # Show main window (ensures canvas and UI elements initialize)
    mw.show()
    app.processEvents()

    canvas = mw.canvas

    # Create an AdditionNode and add to canvas
    node = canvas._create_node_by_class_name("AdditionNode", {"name": "Add1"})
    node_item = canvas.add_node_item(node, x=100, y=100)

    log.debug("Created node %s with initial value=%s", node.name, node.value)

    # Edit node value via NodeEditorDialog (simulate user typing and pressing OK)
    dlg = NodeEditorDialog(node)
    vm_dialog = dlg._dlg
    val_w = vm_dialog._widgets.get("value")
    if val_w is None:
        raise RuntimeError("Value widget missing in node editor")

    # Variant A: set via text box
    new_val_text = "7"
    try:
        if hasattr(val_w, "setPlainText"):
            val_w.setPlainText(new_val_text)
        elif hasattr(val_w, "setText"):
            val_w.setText(new_val_text)
        elif hasattr(val_w, "setValue"):
            val_w.setValue(float(new_val_text))
        else:
            # Fallback: set via VM directly
            vm_dialog.vm.set_value(new_val_text)
    except Exception:
        log.exception("Failed to set value via widget; falling back to VM.set_value")
        try:
            vm_dialog.vm.set_value(new_val_text)
        except Exception:
            pass

    # Process events to let any deferred callbacks run
    app.processEvents()
    time.sleep(0.05)
    app.processEvents()

    log.debug("Applying dialog OK with text=%r (variant A)", new_val_text)
    vm_dialog._on_ok()
    app.processEvents()
    log.debug("After apply (A): node.value=%r", node.value)

    # Variant B: set via VM property directly (simulate programmatic change)
    log.debug("Setting value via VM.set_property (variant B) to 11")
    vm_dialog.vm.set_property("value", 11)
    app.processEvents()
    log.debug("After VM.set_property: node.value=%r", node.value)

    # Variant C: if any numeric parameter widgets exist, try setting them
    if "value" in vm_dialog._widgets:
        w = vm_dialog._widgets["value"]
        try:
            if hasattr(w, "setValue"):
                w.setValue(3.14)
                app.processEvents()
                time.sleep(0.02)
                app.processEvents()
                vm_dialog._on_ok()
                app.processEvents()
                log.debug("After numeric widget set: node.value=%r", node.value)
        except Exception:
            pass

    # Start continuous graph execution (background) to more closely reproduce user scenario
    import traceback
    import types

    # Instrument node.value assignments to trace who sets it
    def _spy_setattr(self, name, val):
        if name == "value":
            log.debug("TRACE: node.__setattr__ setting 'value' to %r", val)
            log.debug("TRACE STACK:\n%s", "\n".join(traceback.format_stack(limit=10)))
        return object.__setattr__(self, name, val)

    # Attach the spy defensively
    if not hasattr(node.__class__, "_orig_setattr"):
        node.__class__._orig_setattr = getattr(node.__class__, "__setattr__", None)
    node.__class__.__setattr__ = _spy_setattr

    # Spy on the node_item.value_label.setPlainText to see when display text changes (defensive)
    try:
        val_label = getattr(node_item, "value_label", None)
        if val_label is not None and hasattr(val_label, "setPlainText"):
            if not hasattr(val_label, "_orig_setPlainText"):
                val_label._orig_setPlainText = val_label.setPlainText

            def _spy_setPlainText(text):
                try:
                    log.debug(
                        "TRACE: NodeItem.value_label.setPlainText called with %r", text
                    )
                    if text == "0":
                        log.warning("TRACE: value_label set to '0' (possible reset)")
                except Exception:
                    log.exception("Error in spy for setPlainText")
                return val_label._orig_setPlainText(text)

            val_label.setPlainText = _spy_setPlainText
    except Exception:
        log.exception("Failed to attach spy to node_item.value_label.setPlainText")

    log.debug("Starting continuous graph execution (play)")
    mw.play_graph()
    # Let it run briefly to allow any UI-driven resets to occur
    time.sleep(0.05)
    app.processEvents()

    # While running, open the NodeEditorDialog for the SAME node and simulate editing to '12'
    try:
        log.debug("Opening NodeEditorDialog for the same node while running")
        dlg_same = NodeEditorDialog(node)
        app.processEvents()
        time.sleep(0.02)
        vm_dialog_same = dlg_same._dlg
        vm = getattr(vm_dialog_same, "vm", None)

        # Spy on VM methods (defensive)
        try:
            if vm is not None:
                if not hasattr(vm, "_orig_set_property") and hasattr(
                    vm, "set_property"
                ):
                    vm._orig_set_property = vm.set_property

                    def _spy_set_property(name, value):
                        log.debug("TRACE: vm.set_property(%r, %r)", name, value)
                        return vm._orig_set_property(name, value)

                    vm.set_property = _spy_set_property

                if not hasattr(vm, "_orig_set_value") and hasattr(vm, "set_value"):
                    vm._orig_set_value = vm.set_value

                    def _spy_set_value(value):
                        log.debug("TRACE: vm.set_value(%r)", value)
                        return vm._orig_set_value(value)

                    vm.set_value = _spy_set_value
        except Exception:
            log.exception("Failed to attach vm spies")

        # Spy on the value widget methods if present
        val_w_same = vm_dialog_same._widgets.get("value")
        try:
            if val_w_same is not None:
                if hasattr(val_w_same, "setPlainText") and not hasattr(
                    val_w_same, "_orig_setPlainText"
                ):
                    val_w_same._orig_setPlainText = val_w_same.setPlainText

                    def _spy_v_setPlainText(txt):
                        log.debug("TRACE: value widget.setPlainText(%r)", txt)
                        return val_w_same._orig_setPlainText(txt)

                    val_w_same.setPlainText = _spy_v_setPlainText

                if hasattr(val_w_same, "setText") and not hasattr(
                    val_w_same, "_orig_setText"
                ):
                    val_w_same._orig_setText = val_w_same.setText

                    def _spy_v_setText(txt):
                        log.debug("TRACE: value widget.setText(%r)", txt)
                        return val_w_same._orig_setText(txt)

                    val_w_same.setText = _spy_v_setText

                if hasattr(val_w_same, "setValue") and not hasattr(
                    val_w_same, "_orig_setValue"
                ):
                    val_w_same._orig_setValue = val_w_same.setValue

                    def _spy_v_setValue(v):
                        log.debug("TRACE: value widget.setValue(%r)", v)
                        return val_w_same._orig_setValue(v)

                    val_w_same.setValue = _spy_v_setValue
        except Exception:
            log.exception("Failed to attach spies to value widget methods")

        # Try to set value to '12' using widget APIs then VM APIs as fallback
        try:
            if val_w_same is not None:
                if hasattr(val_w_same, "setPlainText"):
                    val_w_same.setPlainText("12")
                elif hasattr(val_w_same, "setText"):
                    val_w_same.setText("12")
                elif hasattr(val_w_same, "setValue"):
                    val_w_same.setValue(12)
                else:
                    raise AttributeError("No suitable widget setter found")
            elif vm is not None:
                if hasattr(vm, "set_value"):
                    vm.set_value("12")
                elif hasattr(vm, "set_property"):
                    vm.set_property("value", 12)
        except Exception:
            log.exception("Failed to set value via widget; falling back to VM")
            try:
                if vm is not None and hasattr(vm, "set_property"):
                    vm.set_property("value", 12)
            except Exception:
                pass

        app.processEvents()
        time.sleep(0.05)
        app.processEvents()

        log.debug("Applying dialog OK (same node) with value 12")
        try:
            vm_dialog_same._on_ok()
        except Exception:
            log.exception("vm_dialog_same._on_ok() failed")
        app.processEvents()
        time.sleep(0.05)
        app.processEvents()

        # Log node.value and display
        log.debug("After editing same-node while running: node.value=%r", node.value)
        try:
            disp = node_item.value_label.toPlainText()
        except Exception:
            disp = None
        log.debug("NodeItem display text after edit: %r", disp)
    except Exception:
        log.exception("Failed during same-node editor interaction while running")

    # Now open editor for a different node to simulate user's sequence (open any node editor)
    other_node = canvas._create_node_by_class_name("DisplayNode", {"name": "Disp1"})
    other_item = canvas.add_node_item(other_node, x=200, y=200)
    log.debug("Opening editor for a different node (Disp1)")
    dlg_other = NodeEditorDialog(other_node)
    app.processEvents()
    time.sleep(0.05)

    # Close other dialog (simulate viewing and close)
    try:
        dlg_other._dlg._on_ok()
    except Exception:
        pass
    app.processEvents()
    time.sleep(0.05)

    log.debug(
        "After opening/closing other editor: node.value=%r, display=%r",
        node.value,
        getattr(node_item, "value_label").toPlainText(),
    )

    # Pause the graph
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

    # Close the main window
    mw.close()

    # Print final state
    print("FINAL: node.value=", node.value)
    print("FINAL: node_item display=", getattr(node_item, "value_label").toPlainText())


if __name__ == "__main__":
    main()

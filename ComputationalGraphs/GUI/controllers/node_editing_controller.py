"""
NodeEditingController - Manages node editing and replacement operations.

Extracted from MainWindow as part of Clean Code refactoring.
Handles node editor dialog, node replacement, and related operations.
"""

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from ..main_window import MainWindow


class NodeEditingController:
    """Controller for node editing and replacement operations."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window

    def edit_node(self, node_item):
        """Open editor dialog for a specific node item.

        Args:
            node_item: The NodeItem to edit
        """
        from ..node_editor_dialog import NodeEditorDialog

        mw = self.main_window
        dialog = NodeEditorDialog(node_item.node, mw)

        if dialog.exec():
            # Update visuals
            # Use NodeItem helper to reset text and re-center label
            try:
                node_item.set_label_text(node_item.node.name)
            except Exception:
                # Fallback to old behavior if NodeItem doesn't have helper
                node_item.label.setPlainText(node_item.node.name)
                try:
                    rect = node_item.label.boundingRect()
                    node_item.label.setPos(-rect.width() / 2, -rect.height() / 2 - 10)
                except Exception:
                    pass
            node_item.update_value_display()
            mw.status_bar.showMessage(f"Node '{node_item.node.name}' updated")

    def replace_node(self, node_item):
        """Prompt user to replace node type and perform swap.

        Args:
            node_item: The NodeItem to replace
        """
        from ..replace_node_dialog import ReplaceNodeDialog

        mw = self.main_window
        dlg = ReplaceNodeDialog(mw)

        if dlg.exec():
            new_type = dlg.selected_type()
            if new_type:
                # Delegate orchestration to canvas
                new_node = None
                try:
                    new_node = mw.canvas.replace_node_item(node_item, new_type)
                except Exception:
                    new_node = None
                if new_node:
                    # Open editor to adjust node parameters right away
                    try:
                        self.edit_node(node_item)
                    except Exception:
                        pass
                    mw.status_bar.showMessage(f"Replaced node with type '{new_type}'")

    def edit_selected_node(self):
        """Open editor for the selected node on canvas."""
        from ..node_item import NodeItem

        mw = self.main_window
        selected = mw.canvas.scene.selectedItems()

        node_items = [item for item in selected if isinstance(item, NodeItem)]

        if not node_items:
            QMessageBox.information(mw, "No Selection", "Please select a node to edit.")
            return

        node_item = node_items[0]
        self.edit_node(node_item)

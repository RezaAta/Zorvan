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
        from ..node_item import NodeItem
        from ..replace_node_dialog import ReplaceNodeDialog

        mw = self.main_window
        dlg = ReplaceNodeDialog(mw)

        if dlg.exec():
            new_type = dlg.selected_type()
            if new_type:
                # Determine current selection of node items on canvas
                selected_items = [
                    it
                    for it in mw.canvas.scene.selectedItems()
                    if isinstance(it, NodeItem)
                ]
                # If multiple nodes are selected and the clicked node is one of them,
                # replace all selected nodes. Otherwise, replace only the clicked node.
                multi_replace = len(selected_items) > 1 and node_item in selected_items
                replaced_count = 0
                if multi_replace:
                    for it in selected_items:
                        try:
                            new_node = mw.canvas.replace_node_item(it, new_type)
                            if new_node:
                                replaced_count += 1
                        except Exception:
                            # continue replacing remaining nodes even if one fails
                            continue
                    mw.status_bar.showMessage(
                        f"Replaced {replaced_count} node(s) with type '{new_type}'"
                    )
                else:
                    # Single node replacement - keep previous behavior (open editor)
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
                        mw.status_bar.showMessage(
                            f"Replaced node with type '{new_type}'"
                        )

    def create_node_from_drop(self, scene_pos, start_node_items):
        """Create a node at scene_pos after asking user for the node type.

        Args:
            scene_pos: QPointF scene position where node should be placed
            start_node_items: list of NodeItem that initiated the connection
        """
        from ..replace_node_dialog import ReplaceNodeDialog

        mw = self.main_window
        dlg = ReplaceNodeDialog(mw)
        if not dlg.exec():
            try:
                mw.status_bar.showMessage("Create node cancelled")
            except Exception:
                pass
            return

        new_type = dlg.selected_type()
        if not new_type:
            try:
                mw.status_bar.showMessage("No node type selected")
            except Exception:
                pass
            return

        canvas = mw.canvas
        # Determine a unique name for new node
        try:
            node_id = len(canvas.node_items)
            base_name = f"{new_type}_{node_id}"
            unique_name = canvas._generate_unique_name(base_name)
        except Exception:
            unique_name = f"{new_type}_0"

        # Use canvas factory to create the node with a name attribute
        new_node = canvas._create_node_by_class_name(
            new_type, attrs={"name": unique_name}
        )
        if new_node is None:
            try:
                mw.status_bar.showMessage(f"Failed to create node of type '{new_type}'")
            except Exception:
                pass
            return

        # Add node with undo support
        try:
            canvas.add_node_with_undo(new_node, scene_pos.x(), scene_pos.y())
        except Exception:
            # fallback to direct add if undo method fails
            try:
                if hasattr(mw, "graph") and mw.graph is not None:
                    mw.graph.AddNode(new_node)
                canvas.add_node_item(new_node, scene_pos.x(), scene_pos.y())
            except Exception:
                pass

        # Connect all start nodes to the new node with undo support
        try:
            for start_item in start_node_items:
                try:
                    if start_item.node != new_node:
                        canvas.add_edge_with_undo(start_item.node, new_node)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            mw.status_bar.showMessage(f"Created {unique_name} and connected")
        except Exception:
            pass

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

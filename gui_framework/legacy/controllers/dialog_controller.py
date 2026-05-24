"""
DialogController - Manages dialog-driven graph creation and example loading.

Extracted from MainWindow as part of Clean Code refactoring.
Handles MLP dialog, Backprop dialog, and example loading functionality.
"""

from typing import TYPE_CHECKING, Callable

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    from ..main_window import MainWindow


class DialogController:
    """Controller for dialog-based graph creation and example loading."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window

    def show_mlp_dialog(self):
        """Show dialog to generate MLP graph."""
        from ..mlp_dialog import MLPGeneratorDialog

        dialog = MLPGeneratorDialog(self.main_window)
        if dialog.exec():
            generated_graph = dialog.get_graph()

            # Clear current canvas
            self.main_window.canvas.scene.clear()
            self.main_window.canvas.node_items.clear()
            self.main_window.canvas.edge_items.clear()

            # Load the generated graph and keep canvas/runner synchronized
            self.main_window.set_graph(generated_graph)
            # DON'T reset when loading - it clears DataStreamNode data!

            # Visualize the graph on canvas
            self.main_window._visualize_graph_on_canvas(generated_graph)
            self.main_window.update_stopping_nodes_display()

            # Apply MLP layout for neural network graphs
            try:
                self.main_window.apply_graph_layout("mlp_layout", spacing=80)
            except Exception as e:
                print(f"[GUI] Failed to apply MLP layout: {e}")

            self.main_window.status_bar.showMessage("MLP generated successfully")

    def show_backprop_dialog(self):
        """Show dialog to add backpropagation to existing MLP."""
        from ..backprop_dialog import BackpropDialog

        if not self.main_window.graph or len(self.main_window.graph.nodes) == 0:
            QMessageBox.warning(
                self.main_window, "No Graph", "Please load or create a graph first."
            )
            return

        dialog = BackpropDialog(self.main_window.graph, self.main_window)
        if dialog.exec():
            generated_graph = dialog.get_graph()

            # Clear current canvas
            self.main_window.canvas.scene.clear()
            self.main_window.canvas.node_items.clear()
            self.main_window.canvas.edge_items.clear()

            # Load the graph with backprop and keep the UI/runner in sync
            self.main_window.set_graph(generated_graph)
            # DON'T reset when loading - it clears DataStreamNode data!

            # Visualize the graph on canvas
            self.main_window._visualize_graph_on_canvas(generated_graph)
            self.main_window.update_stopping_nodes_display()

            # Apply MLP layout for neural network graphs
            try:
                self.main_window.apply_graph_layout("mlp_layout", spacing=80)
            except Exception as e:
                print(f"[GUI] Failed to apply MLP layout: {e}")

            self.main_window.status_bar.showMessage(
                "Backpropagation added successfully"
            )

    def populate_examples_menu(self, menu):
        """Populate the examples menu with categories. Prefer repository-provided examples when available."""
        # If examples_repository present, use its categorized view
        repo = getattr(self.main_window, "examples_repository", None)
        if repo is not None:
            try:
                cats = repo.list_examples_by_category()
                if cats:
                    for cat_name, examples in cats.items():
                        category_menu = menu.addMenu(cat_name)
                        for name, desc, builder in examples:
                            action = QAction(name, self.main_window)
                            action.setStatusTip(desc)
                            # Use repository.build wrapper so repository can control building and error handling
                            action.triggered.connect(
                                lambda checked, repo=repo, n=name: self.load_example(
                                    lambda: repo.build(n), n
                                )
                            )
                            category_menu.addAction(action)
                    return
            except Exception:
                # Fall back to legacy examples loader on error
                pass

        # Legacy fallback: use ExamplesLoader categories
        for category in self.main_window.examples_loader.get_categories():
            category_menu = menu.addMenu(category.name)
            category_menu.setToolTip(category.description)

            for name, description, builder in category.examples:
                action = QAction(name, self.main_window)
                action.setStatusTip(description)
                action.triggered.connect(
                    lambda checked, b=builder, n=name: self.load_example(b, n)
                )
                category_menu.addAction(action)

        # Add action to save current layout for the last loaded example
        try:
            save_action = QAction("Save Current Layout", self.main_window)
            save_action.setStatusTip(
                "Save current canvas positions for the last loaded example"
            )
            save_action.triggered.connect(lambda: self.save_current_example_layout())
            menu.addSeparator()
            menu.addAction(save_action)
        except Exception:
            pass

    def load_example(self, builder: Callable, name: str):
        """Load an example graph.

        Args:
            builder: Function that builds and returns the example graph
            name: Display name of the example
        """
        import time

        try:
            # Build the example graph (log timing to help identify where GUI may freeze)
            build_t0 = time.time()
            try:
                self.main_window.status_bar.showMessage(f"Building example: {name}...")
            except Exception:
                pass
            print(f"[GUI] Starting builder for example: {name}")
            example_graph = builder()
            # Defensive check: if builder returns None, surface friendly error and abort
            if example_graph is None:
                try:
                    self.main_window.status_bar.showMessage(
                        f"Failed to build example: {name} (builder returned None)"
                    )
                except Exception:
                    pass
                try:
                    QMessageBox.warning(
                        self.main_window,
                        "Error Loading Example",
                        f"Builder for example '{name}' returned no graph.",
                    )
                except Exception:
                    pass
                return
            build_t1 = time.time()
            print(
                f"[GUI] Builder complete for example: {name} (duration: {build_t1 - build_t0:.3f}s)"
            )

            # Apply any saved layout metadata to the freshly built graph before visualization
            try:
                repo = getattr(self.main_window, "examples_repository", None)
                if repo is not None:
                    layout = repo.load_layout(name)
                    if layout:
                        # layout: {node_id: {"gui_pos": [x,y], "gui_color": ..., ...}}
                        for node in example_graph.nodes:
                            node_layout = layout.get(getattr(node, "id", None))
                            if node_layout:
                                if "gui_pos" in node_layout:
                                    node.gui_pos = tuple(node_layout["gui_pos"])
                                if "gui_color" in node_layout:
                                    node.gui_color = node_layout["gui_color"]
                                if "gui_radius" in node_layout:
                                    node.gui_radius = node_layout["gui_radius"]
                                if "gui_label" in node_layout:
                                    node.gui_label = node_layout["gui_label"]
                                if "gui_label_color" in node_layout:
                                    node.gui_label_color = node_layout[
                                        "gui_label_color"
                                    ]
            except Exception:
                pass
            try:
                self.main_window.status_bar.showMessage(
                    f"Building example: {name} done ({len(example_graph.nodes)} nodes)"
                )
            except Exception:
                pass

            # Clear current canvas
            try:
                self.main_window.canvas.scene.clear()
                self.main_window.canvas.node_items.clear()
                self.main_window.canvas.edge_items.clear()
            except Exception:
                pass

            # Load the new graph and synchronize canvas and runner
            self.main_window.set_graph(example_graph)

            # NOTE: perform a full reset for examples so execution controls reflect
            # the freshly-loaded graph (this intentionally clears processor state)

            # Visualize the graph on canvas (log timing)
            vis_t0 = time.time()
            try:
                self.main_window.status_bar.showMessage(
                    f"Applying layout and visualizing example: {name}..."
                )
            except Exception:
                pass
            print(
                f"[GUI] Visualizing example: {name} - starting visualization with {len(example_graph.nodes)} nodes"
            )
            try:
                self.main_window._visualize_graph_on_canvas(example_graph)
            except Exception:
                pass
            vis_t1 = time.time()
            print(
                f"[GUI] Visualization complete for example: {name} (duration: {vis_t1 - vis_t0:.3f}s)"
            )

            # Reset execution controls and processor so the UI is in a stopped/default state
            try:
                self.main_window.reset_graph()
            except Exception:
                pass

            # Process any pending Qt events to flush stale step_completed signals
            try:
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()
            except Exception:
                pass

            # Explicitly ensure step counter displays 0 (guard against stale queued signals)
            try:
                max_steps = self.main_window.max_steps_spin.value()
                self.main_window.step_label.setText(f"Step: 0 / {max_steps}")
                if (
                    hasattr(self.main_window, "step_progress")
                    and self.main_window.step_progress
                ):
                    self.main_window.step_progress.setValue(0)
                    self.main_window.step_progress.setMaximum(max_steps)
            except Exception:
                pass

            # Force UI refresh so step counter displays immediately
            try:
                from PyQt6.QtWidgets import QApplication

                QApplication.processEvents()
            except Exception:
                pass

            try:
                self.main_window.status_bar.showMessage(
                    f"Loaded example: {name} (build {build_t1 - build_t0:.3f}s, vis {vis_t1 - vis_t0:.3f}s)"
                )
            except Exception:
                pass

            # Update starting nodes display
            try:
                self.main_window.update_starting_nodes_display()
            except Exception:
                pass
            try:
                self.main_window.update_stopping_nodes_display()
            except Exception:
                pass

            # Check if this is an MLP example and apply MLP layout automatically
            is_mlp_example = any(
                keyword in name.lower()
                for keyword in ["mlp", "xor", "iris", "diabetes", "piecewise", "neural"]
            )
            if is_mlp_example:
                try:
                    # Apply MLP layout with 80px spacing (grid cell size)
                    self.main_window.apply_graph_layout("mlp_layout", spacing=80)
                    print(f"[GUI] Applied MLP Layout for example: {name}")
                except Exception as e:
                    print(f"[GUI] Failed to apply MLP layout: {e}")
            else:
                # Apply Tree layout as default for non-neural network examples
                try:
                    self.main_window.apply_graph_layout("tree", spacing=80)
                    print(f"[GUI] Applied Tree Layout for example: {name}")
                except Exception as e:
                    print(f"[GUI] Failed to apply Tree layout: {e}")

            try:
                self.main_window.status_bar.showMessage(f"Loaded example: {name}")
            except Exception:
                pass

            # Record last loaded example name to enable saving layout
            try:
                self.main_window.last_loaded_example_name = name
            except Exception:
                pass

            # --- SYNC: Rebuild canonical graph map and ensure canvas items are bound ---
            try:
                self._sync_graph_after_load()
            except Exception:
                pass
        except Exception as e:
            import traceback

            full_error = traceback.format_exc()
            print(f"\n{'='*60}")
            print(f"ERROR loading example '{name}':")
            print(full_error)
            print(f"{'='*60}\n")
            try:
                QMessageBox.critical(
                    self.main_window,
                    "Error Loading Example",
                    f"Failed to load example '{name}':\n{str(e)}\n\nSee console for full traceback.",
                )
            except Exception:
                pass

    def save_current_example_layout(self):
        """Save current canvas/node layout for the last loaded example name using ExamplesRepository."""
        try:
            repo = getattr(self.main_window, "examples_repository", None)
            name = getattr(self.main_window, "last_loaded_example_name", None)
            if repo is None or not name:
                QMessageBox.warning(
                    self.main_window,
                    "Save Layout",
                    "No example loaded or repository unavailable.",
                )
                return False

            graph = getattr(self.main_window, "graph", None)
            canvas = getattr(self.main_window, "canvas", None)
            if graph is None or canvas is None:
                QMessageBox.warning(
                    self.main_window,
                    "Save Layout",
                    "No graph/canvas available to save layout from.",
                )
                return False

            layout = {}
            for node in graph.nodes:
                nid = getattr(node, "id", None)
                if nid is None:
                    continue
                node_item = canvas.node_items.get(node)
                if node_item is None:
                    continue
                # Collect attributes
                pos = (node_item.pos().x(), node_item.pos().y())
                entry = {"gui_pos": pos}
                manual_color = getattr(node_item, "manual_color", None)
                if manual_color is not None:
                    try:
                        entry["gui_color"] = manual_color.name()
                    except Exception:
                        pass
                if getattr(node_item, "radius", None) is not None:
                    entry["gui_radius"] = node_item.radius
                try:
                    entry["gui_label"] = node_item.label.toPlainText()
                except Exception:
                    pass
                try:
                    entry["gui_label_color"] = node_item.label.defaultTextColor().name()
                except Exception:
                    pass
                layout[nid] = entry

            ok = repo.save_layout(name, layout)
            if ok:
                try:
                    self.main_window.status_bar.showMessage(
                        f"Saved layout for example: {name}"
                    )
                except Exception:
                    pass
            else:
                QMessageBox.warning(
                    self.main_window,
                    "Save Layout",
                    "Failed to save layout to repository.",
                )
            return ok
        except Exception:
            return False

    def _sync_graph_after_load(self):
        """Rebuild canonical graph map and ensure canvas items are bound after loading."""
        try:
            # Rebuild adjacency matrix & id dictionary in case builder used nonstandard manipulations
            if (
                hasattr(self.main_window, "graph")
                and self.main_window.graph is not None
            ):
                try:
                    self.main_window.graph.UpdateAdjacencyMatrix()
                    # Rebuild id map (safeguard if any missing ids)
                    try:
                        self.main_window.graph.idToNodeDictionary = {
                            n.id: n
                            for n in self.main_window.graph.nodes
                            if getattr(n, "id", None) is not None
                        }
                    except Exception:
                        pass
                except Exception:
                    pass

            # Reattach canvas reference and refresh visuals for all NodeItems
            try:
                if (
                    hasattr(self.main_window, "canvas")
                    and self.main_window.canvas is not None
                ):
                    for node_obj, node_item in list(
                        getattr(self.main_window.canvas, "node_items", {}).items()
                    ):
                        try:
                            node_item.canvas = self.main_window.canvas
                        except Exception:
                            pass
                        try:
                            # Refresh node label and value display if widget methods exist
                            if hasattr(node_item, "set_label_text"):
                                node_item.set_label_text(
                                    getattr(node_item.node, "name", "")
                                )
                            if hasattr(node_item, "update_value_display"):
                                node_item.update_value_display()
                        except Exception:
                            pass
                    try:
                        # Ensure canvas repaints and the QGraphicsScene knows of the nodes
                        self.main_window.canvas.scene.update()
                        try:
                            self.main_window.canvas.viewport().update()
                        except Exception:
                            pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

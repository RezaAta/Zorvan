"""
DialogController - Manages dialog-driven graph creation and example loading.

Extracted from MainWindow as part of Clean Code refactoring.
Handles MLP dialog, Backprop dialog, and example loading functionality.
"""
from typing import TYPE_CHECKING, Callable

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QAction

if TYPE_CHECKING:
    from ..main_window import MainWindow


class DialogController:
    """Controller for dialog-based graph creation and example loading."""
    
    def __init__(self, main_window: 'MainWindow'):
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
                self.main_window.apply_graph_layout('mlp_layout', spacing=80)
            except Exception as e:
                print(f"[GUI] Failed to apply MLP layout: {e}")
            
            self.main_window.status_bar.showMessage("MLP generated successfully")
    
    def show_backprop_dialog(self):
        """Show dialog to add backpropagation to existing MLP."""
        from ..backprop_dialog import BackpropDialog
        
        if not self.main_window.graph or len(self.main_window.graph.nodes) == 0:
            QMessageBox.warning(
                self.main_window,
                "No Graph",
                "Please load or create a graph first."
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
                self.main_window.apply_graph_layout('mlp_layout', spacing=80)
            except Exception as e:
                print(f"[GUI] Failed to apply MLP layout: {e}")
            
            self.main_window.status_bar.showMessage("Backpropagation added successfully")
    
    def populate_examples_menu(self, menu):
        """Populate the examples menu with categories."""
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
            self.main_window.status_bar.showMessage(f"Building example: {name}...")
            print(f"[GUI] Starting builder for example: {name}")
            example_graph = builder()
            build_t1 = time.time()
            print(f"[GUI] Builder complete for example: {name} (duration: {build_t1 - build_t0:.3f}s)")
            try:
                self.main_window.status_bar.showMessage(
                    f"Building example: {name} done ({len(example_graph.nodes)} nodes)"
                )
            except Exception:
                pass
            
            # Clear current canvas
            self.main_window.canvas.scene.clear()
            self.main_window.canvas.node_items.clear()
            self.main_window.canvas.edge_items.clear()
            
            # Load the new graph and synchronize canvas and runner
            self.main_window.set_graph(example_graph)
            
            # DON'T reset when loading - it clears DataStreamNode data!
            
            # Visualize the graph on canvas (log timing)
            vis_t0 = time.time()
            self.main_window.status_bar.showMessage(f"Applying layout and visualizing example: {name}...")
            print(f"[GUI] Visualizing example: {name} - starting visualization with {len(example_graph.nodes)} nodes")
            self.main_window._visualize_graph_on_canvas(example_graph)
            vis_t1 = time.time()
            print(f"[GUI] Visualization complete for example: {name} (duration: {vis_t1 - vis_t0:.3f}s)")
            self.main_window.status_bar.showMessage(
                f"Loaded example: {name} (build {build_t1 - build_t0:.3f}s, vis {vis_t1 - vis_t0:.3f}s)"
            )
            
            # Update starting nodes display
            self.main_window.update_starting_nodes_display()
            self.main_window.update_stopping_nodes_display()
            
            # Check if this is an MLP example and apply MLP layout automatically
            is_mlp_example = any(
                keyword in name.lower() 
                for keyword in ['mlp', 'xor', 'iris', 'diabetes', 'piecewise', 'neural']
            )
            if is_mlp_example:
                try:
                    # Apply MLP layout with 80px spacing (grid cell size)
                    self.main_window.apply_graph_layout('mlp_layout', spacing=80)
                    print(f"[GUI] Applied MLP Layout for example: {name}")
                except Exception as e:
                    print(f"[GUI] Failed to apply MLP layout: {e}")
            else:
                # Apply Tree layout as default for non-neural network examples
                try:
                    self.main_window.apply_graph_layout('tree', spacing=80)
                    print(f"[GUI] Applied Tree Layout for example: {name}")
                except Exception as e:
                    print(f"[GUI] Failed to apply Tree layout: {e}")
            
            self.main_window.status_bar.showMessage(f"Loaded example: {name}")

            # --- SYNC: Rebuild canonical graph map and ensure canvas items are bound ---
            self._sync_graph_after_load()
            
        except Exception as e:
            import traceback
            full_error = traceback.format_exc()
            print(f"\n{'='*60}")
            print(f"ERROR loading example '{name}':")
            print(full_error)
            print(f"{'='*60}\n")
            QMessageBox.critical(
                self.main_window,
                "Error Loading Example",
                f"Failed to load example '{name}':\n{str(e)}\n\nSee console for full traceback."
            )
    
    def _sync_graph_after_load(self):
        """Rebuild canonical graph map and ensure canvas items are bound after loading."""
        try:
            # Rebuild adjacency matrix & id dictionary in case builder used nonstandard manipulations
            if hasattr(self.main_window, 'graph') and self.main_window.graph is not None:
                try:
                    self.main_window.graph.UpdateAdjacencyMatrix()
                    # Rebuild id map (safeguard if any missing ids)
                    try:
                        self.main_window.graph.idToNodeDictionary = {
                            n.id: n for n in self.main_window.graph.nodes 
                            if getattr(n, 'id', None) is not None
                        }
                    except Exception:
                        pass
                except Exception:
                    pass

            # Reattach canvas reference and refresh visuals for all NodeItems
            try:
                if hasattr(self.main_window, 'canvas') and self.main_window.canvas is not None:
                    for node_obj, node_item in list(
                        getattr(self.main_window.canvas, 'node_items', {}).items()
                    ):
                        try:
                            node_item.canvas = self.main_window.canvas
                        except Exception:
                            pass
                        try:
                            # Refresh node label and value display if widget methods exist
                            if hasattr(node_item, 'set_label_text'):
                                node_item.set_label_text(getattr(node_item.node, 'name', ''))
                            if hasattr(node_item, 'update_value_display'):
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

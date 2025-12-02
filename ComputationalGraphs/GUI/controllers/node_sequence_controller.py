"""
Node Sequence Controller - handles starting/stopping nodes and manual sequence management.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages the Forward Processing starting/stopping nodes and
Manual Processing sequence configuration.
"""

from PyQt6.QtWidgets import QMessageBox


class NodeSequenceController:
    """Controller for node sequence management.
    
    Manages starting nodes (for Forward Processing), stopping nodes,
    and manual processing sequences.
    """
    
    def __init__(self, main_window):
        """Initialize the node sequence controller.
        
        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
    
    @property
    def graph(self):
        """Access the current graph from main window."""
        return self.main_window.graph
    
    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas
    
    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar
    
    @property
    def starting_nodes_list(self):
        """Access the starting nodes list widget."""
        return self.main_window.starting_nodes_list
    
    @property
    def stopping_nodes_list(self):
        """Access the stopping nodes list widget."""
        return self.main_window.stopping_nodes_list
    
    @property
    def manual_sequence_list(self):
        """Access the manual sequence list widget."""
        return self.main_window.manual_sequence_list
    
    # --- Starting Nodes Management ---
    
    def update_starting_nodes_display(self):
        """Update the starting nodes list display."""
        self.starting_nodes_list.clear()
        
        if not self.graph:
            return
        
        # Check if graph has starting_nodes attribute
        if hasattr(self.graph, 'starting_nodes') and self.graph.starting_nodes:
            for node in self.graph.starting_nodes:
                self.starting_nodes_list.addItem(node.name)
        else:
            # Auto-detect nodes with no predecessors and show in gray (not set)
            source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
            for node in source_nodes:
                item_text = f"(auto) {node.name}"
                self.starting_nodes_list.addItem(item_text)
    
    def add_selected_to_starting_nodes(self):
        """Add selected nodes from canvas to starting nodes list."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return
        
        # Get selected nodes from canvas
        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]
        
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) on the canvas first.")
            return
        
        # Initialize starting_nodes if not exists
        if not hasattr(self.graph, 'starting_nodes') or self.graph.starting_nodes is None:
            self.graph.starting_nodes = []
        
        # Add selected nodes to starting_nodes (avoid duplicates)
        added_count = 0
        for item in selected_items:
            if item.node not in self.graph.starting_nodes:
                self.graph.starting_nodes.append(item.node)
                added_count += 1
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Added {added_count} node(s) to starting nodes")
    
    def remove_from_starting_nodes(self):
        """Remove selected nodes from starting nodes list."""
        if not self.graph or not hasattr(self.graph, 'starting_nodes') or not self.graph.starting_nodes:
            return
        
        # Get selected items from the list
        selected_items = self.starting_nodes_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) from the starting nodes list.")
            return
        
        # Remove nodes by name
        removed_count = 0
        for item in selected_items:
            node_name = item.text().replace("(auto) ", "")  # Remove auto prefix if present
            # Find and remove the node
            for node in self.graph.starting_nodes[:]:  # Use slice to modify while iterating
                if node.name == node_name:
                    self.graph.starting_nodes.remove(node)
                    removed_count += 1
                    break
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Removed {removed_count} node(s) from starting nodes")
    
    def auto_detect_starting_nodes(self):
        """Auto-detect starting nodes (nodes with no predecessors)."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return
        
        # Find nodes with no predecessors
        source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
        
        if not source_nodes:
            QMessageBox.warning(self.main_window, "No Sources Found", 
                              "No nodes with zero predecessors found.\n"
                              "Graph may have cycles or all nodes have inputs.")
            return
        
        # Set as starting nodes
        self.graph.starting_nodes = source_nodes
        self.update_starting_nodes_display()
        self.status_bar.showMessage(f"Auto-detected {len(source_nodes)} starting node(s)")
    
    def clear_starting_nodes(self):
        """Clear all starting nodes."""
        if not self.graph:
            return
        
        if hasattr(self.graph, 'starting_nodes'):
            self.graph.starting_nodes = []
        
        self.update_starting_nodes_display()
        self.status_bar.showMessage("Cleared all starting nodes")
    
    # --- Stopping Nodes Management ---
    
    def update_stopping_nodes_display(self):
        """Update the stopping nodes list display."""
        self.stopping_nodes_list.clear()

        if not self.graph:
            return

        if hasattr(self.graph, 'stopping_nodes') and self.graph.stopping_nodes:
            for node in self.graph.stopping_nodes:
                self.stopping_nodes_list.addItem(node.name)

    def add_selected_to_stopping_nodes(self):
        """Add selected nodes from canvas to stopping nodes list."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]

        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) on the canvas first.")
            return

        if not hasattr(self.graph, 'stopping_nodes') or self.graph.stopping_nodes is None:
            self.graph.stopping_nodes = []

        added_count = 0
        for item in selected_items:
            if item.node not in self.graph.stopping_nodes:
                self.graph.stopping_nodes.append(item.node)
                added_count += 1

        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Added {added_count} node(s) to stopping nodes")

    def remove_from_stopping_nodes(self):
        """Remove selected nodes from stopping nodes list."""
        if not self.graph or not hasattr(self.graph, 'stopping_nodes') or not self.graph.stopping_nodes:
            return

        selected_items = self.stopping_nodes_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) from the stopping nodes list.")
            return

        removed_count = 0
        for item in selected_items:
            node_name = item.text()
            for node in self.graph.stopping_nodes[:]:
                if node.name == node_name:
                    self.graph.stopping_nodes.remove(node)
                    removed_count += 1
                    break

        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Removed {removed_count} node(s) from stopping nodes")

    def auto_detect_stopping_nodes(self):
        """Auto-detect stopping nodes (ContainerNodes / weights)."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
        candidates = [n for n in self.graph.nodes if isinstance(n, ContainerNode)]

        if not candidates:
            QMessageBox.warning(self.main_window, "No Candidates", 
                               "No ContainerNode candidates found.")
            return

        self.graph.stopping_nodes = candidates
        self.update_stopping_nodes_display()
        self.status_bar.showMessage(f"Auto-detected {len(candidates)} stopping node(s)")

    def clear_stopping_nodes(self):
        """Clear all stopping nodes."""
        if not self.graph:
            return

        if hasattr(self.graph, 'stopping_nodes'):
            self.graph.stopping_nodes = []

        self.update_stopping_nodes_display()
        self.status_bar.showMessage("Cleared all stopping nodes")
    
    # --- Manual Sequence Management ---
    
    def add_selected_to_manual_sequence(self):
        """Add a step to the manual sequence using currently selected nodes on canvas."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) on the canvas first.")
            return

        step_nodes = [item.node for item in selected_items]
        # Append step (list of Node objects) to manual sequence UI and graph property
        if not hasattr(self.graph, 'manual_processing_sequence') or self.graph.manual_processing_sequence is None:
            self.graph.manual_processing_sequence = []
        self.graph.manual_processing_sequence.append(step_nodes)
        step_label = f"Step {len(self.graph.manual_processing_sequence)-1}: " + ", ".join([n.name for n in step_nodes])
        self.manual_sequence_list.addItem(step_label)
        self.status_bar.showMessage("Added manual sequence step (Selected nodes)")

    def add_selected_nodes_to_selected_step(self):
        """Append currently selected canvas nodes to the chosen manual sequence step."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        # Determine the selected step (use first selected entry)
        selected_steps = self.manual_sequence_list.selectedItems()
        if not selected_steps:
            QMessageBox.information(self.main_window, "No Step Selected", 
                                   "Please select a manual sequence step in the list.")
            return
        step_index = self.manual_sequence_list.row(selected_steps[0])

        # Get selected nodes from canvas
        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) on the canvas first.")
            return

        nodes_to_add = [item.node for item in selected_items]

        if not hasattr(self.graph, 'manual_processing_sequence') or self.graph.manual_processing_sequence is None:
            self.graph.manual_processing_sequence = []

        # Ensure the step exists (expand list if necessary)
        while len(self.graph.manual_processing_sequence) <= step_index:
            self.graph.manual_processing_sequence.append([])

        step = self.graph.manual_processing_sequence[step_index]
        added = 0
        for n in nodes_to_add:
            if n not in step:
                step.append(n)
                added += 1

        # Update UI entry
        labels = [n.name for n in step]
        self.manual_sequence_list.item(step_index).setText(f"Step {step_index}: " + ", ".join(labels))
        self.status_bar.showMessage(f"Added {added} node(s) to Step {step_index}")

    def replace_selected_step_with_selected_nodes(self):
        """Replace the chosen manual sequence step contents with the currently selected canvas nodes."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        selected_steps = self.manual_sequence_list.selectedItems()
        if not selected_steps:
            QMessageBox.information(self.main_window, "No Step Selected", 
                                   "Please select a manual sequence step in the list.")
            return
        step_index = self.manual_sequence_list.row(selected_steps[0])

        selected_items = [item for item in self.canvas.scene.selectedItems() 
                         if hasattr(item, 'node')]
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select node(s) on the canvas first.")
            return

        nodes_to_set = [item.node for item in selected_items]

        if not hasattr(self.graph, 'manual_processing_sequence') or self.graph.manual_processing_sequence is None:
            self.graph.manual_processing_sequence = []

        while len(self.graph.manual_processing_sequence) <= step_index:
            self.graph.manual_processing_sequence.append([])

        self.graph.manual_processing_sequence[step_index] = list(nodes_to_set)

        # Update UI entry
        labels = [n.name for n in nodes_to_set]
        self.manual_sequence_list.item(step_index).setText(f"Step {step_index}: " + ", ".join(labels))
        self.status_bar.showMessage(f"Replaced Step {step_index} with {len(nodes_to_set)} node(s)")

    def remove_from_manual_sequence(self):
        """Remove selected step(s) from manual sequence UI and update graph property."""
        if not self.graph or not hasattr(self.graph, 'manual_processing_sequence') or not self.graph.manual_processing_sequence:
            QMessageBox.information(self.main_window, "No Sequence", "Manual sequence is empty.")
            return

        selected_items = self.manual_sequence_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self.main_window, "No Selection", 
                                   "Please select step(s) from the manual sequence list.")
            return

        for item in selected_items:
            row = self.manual_sequence_list.row(item)
            self.manual_sequence_list.takeItem(row)
            try:
                del self.graph.manual_processing_sequence[row]
            except Exception:
                pass

        # Rebuild displayed labels to reflect new indices
        self.load_manual_sequence_from_graph()
        self.status_bar.showMessage("Removed selected step(s) from manual sequence")

    def clear_manual_sequence(self):
        """Clear manual sequence from UI and graph property."""
        self.manual_sequence_list.clear()
        if hasattr(self.graph, 'manual_processing_sequence'):
            try:
                self.graph.manual_processing_sequence = None
            except Exception:
                pass
        self.status_bar.showMessage("Manual sequence cleared")

    def apply_manual_sequence_to_graph(self):
        """Take steps from UI list and set the graph manual_processing_sequence property accordingly."""
        if not self.graph:
            QMessageBox.warning(self.main_window, "No Graph", "Please load a graph first.")
            return

        sequence = []
        for i in range(self.manual_sequence_list.count()):
            item_text = self.manual_sequence_list.item(i).text()
            # Format: "Step N: a, b, c"
            if ':' in item_text:
                _, nodes_str = item_text.split(':', 1)
                node_names = [n.strip() for n in nodes_str.split(',') if n.strip()]
            else:
                node_names = [n.strip() for n in item_text.split(',') if n.strip()]

            # Resolve node names to Node objects or pass through id strings
            step = []
            for nm in node_names:
                # If name matches a node id, prefer id
                if nm in self.graph.idToNodeDictionary:
                    step.append(self.graph.idToNodeDictionary[nm])
                else:
                    # match by node name
                    matches = [n for n in self.graph.nodes if getattr(n, 'name', None) == nm]
                    if matches:
                        step.append(matches[0])
                    else:
                        # Fall back to string name
                        step.append(nm)
            sequence.append(step)

        try:
            self.graph.set_manual_processing_sequence(sequence, strict=False)
            self.status_bar.showMessage("Manual sequence applied to graph")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Apply Failed", 
                                f"Failed to set manual sequence: {e}")

    def load_manual_sequence_from_graph(self):
        """Load the current graph.manual_processing_sequence into the UI list."""
        self.manual_sequence_list.clear()
        if not self.graph or not hasattr(self.graph, 'manual_processing_sequence') or not self.graph.manual_processing_sequence:
            return

        for i, step in enumerate(self.graph.manual_processing_sequence):
            try:
                labels = [n.name if hasattr(n, 'name') else (n.id if hasattr(n, 'id') else str(n)) for n in step]
                step_label = f"Step {i}: " + ", ".join(labels)
            except Exception:
                step_label = f"Step {i}"
            self.manual_sequence_list.addItem(step_label)

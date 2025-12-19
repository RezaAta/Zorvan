#!/usr/bin/env python3
"""
Test application for CanvasView - Stage 2 (Interaction).

Creates a simple graph and displays it in the new CanvasView.
Tests zoom, pan, dragging, selection, and interaction.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
    from PyQt6.QtCore import Qt
    HAS_PYQT = True
except ImportError:
    print("PyQt6 not installed. Install with: pip install PyQt6")
    HAS_PYQT = False
    sys.exit(1)

from gui_framework.viewmodels.canvas_viewmodel import CanvasViewModel
from gui_framework.views.canvas_view import CanvasView


class MockNode:
    """Mock computational graph node."""
    
    def __init__(self, name, x=0, y=0):
        self.name = name
        self.x = x
        self.y = y
        self.predecessors = []


class MockGraph:
    """Mock computational graph."""
    
    def __init__(self):
        self.nodes = []


def create_test_graph():
    """Create a simple test graph."""
    graph = MockGraph()
    
    # Create nodes in a simple layout
    node_a = MockNode("Input A", -200, -100)
    node_b = MockNode("Input B", -200, 100)
    node_c = MockNode("Process", 0, 0)
    node_d = MockNode("Output", 200, 0)
    
    # Set up connections
    node_c.predecessors = [node_a, node_b]
    node_d.predecessors = [node_c]
    
    graph.nodes = [node_a, node_b, node_c, node_d]
    return graph


class TestCanvasWindow(QMainWindow):
    """Test window for canvas view."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CanvasView Test - Stage 3 (Commands & Undo/Redo)")
        self.setMinimumSize(1000, 700)
        
        # Create central widget
        central = QWidget()
        main_layout = QVBoxLayout()
        
        # Create test graph
        self.graph = create_test_graph()
        
        # Create ViewModel and View
        self.canvas_vm = CanvasViewModel(self.graph)
        self.canvas_view = CanvasView(self.canvas_vm)
        
        main_layout.addWidget(self.canvas_view)
        
        # Status label
        self.status_label = QLabel("Stage 3: Commands & Undo/Redo Enabled")
        self.status_label.setStyleSheet("padding: 5px; background: #E8F5E9; border: 1px solid #4CAF50;")
        main_layout.addWidget(self.status_label)
        
        # Add control buttons
        controls_layout = QHBoxLayout()
        
        # Undo/Redo buttons (Stage 3)
        undo_btn = QPushButton("Undo (Ctrl+Z)")
        undo_btn.clicked.connect(lambda: self.canvas_view.undo_stack.undo() if self.canvas_view.undo_stack else None)
        controls_layout.addWidget(undo_btn)
        
        redo_btn = QPushButton("Redo (Ctrl+Shift+Z)")
        redo_btn.clicked.connect(lambda: self.canvas_view.undo_stack.redo() if self.canvas_view.undo_stack else None)
        controls_layout.addWidget(redo_btn)
        
        controls_layout.addWidget(QLabel("|"))
        
        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.clicked.connect(self.canvas_vm.zoom_in)
        controls_layout.addWidget(zoom_in_btn)
        
        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.clicked.connect(self.canvas_vm.zoom_out)
        controls_layout.addWidget(zoom_out_btn)
        
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(self.canvas_vm.reset_viewport)
        controls_layout.addWidget(reset_btn)
        
        controls_layout.addWidget(QLabel("|"))
        
        color_btn = QPushButton("Color Node C")
        color_btn.clicked.connect(self._color_node_c)
        controls_layout.addWidget(color_btn)
        
        active_btn = QPushButton("Toggle Node C Active")
        active_btn.clicked.connect(self._toggle_active)
        controls_layout.addWidget(active_btn)
        
        controls_layout.addWidget(QLabel("|"))
        
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        controls_layout.addWidget(select_all_btn)
        
        clear_btn = QPushButton("Clear Selection")
        clear_btn.clicked.connect(self._clear_selection)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        main_layout.addLayout(controls_layout)
        
        central.setLayout(main_layout)
        self.setCentralWidget(central)
        
        self._node_c_active = False
        
        # Update status label periodically
        from PyQt6.QtCore import QTimer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(500)  # Update every 500ms
        
        print("\n" + "="*60)
        print("CanvasView Test Application - Stage 3")
        print("="*60)
        print("\nFeatures:")
        print("- Graph with 4 nodes and 3 edges")
        print("- Zoom in/out with buttons or mouse wheel")
        print("- Drag nodes to move them")
        print("- Click nodes to select (Ctrl+Click to add to selection)")
        print("- Drag on empty area for rubber band selection")
        print("- Ctrl+A to select all")
        print("- Delete key to delete selected (placeholder)")
        print("- Undo/Redo support:")
        print("  * Ctrl+Z to undo")
        print("  * Ctrl+Shift+Z or Ctrl+Y to redo")
        print("  * Undo/Redo buttons in toolbar")
        print("- Node coloring test")
        print("- Active node highlighting test")
        print("\nStage 3: Commands & Undo/Redo enabled")
        print("="*60 + "\n")
    
    def _color_node_c(self):
        """Test node coloring."""
        import random
        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", None]
        color = random.choice(colors)
        self.canvas_vm.set_node_color("Process", color)
        print(f"[Test] Set Process node color to: {color or 'default'}")
    
    def _toggle_active(self):
        """Test active node highlighting."""
        self._node_c_active = not self._node_c_active
        self.canvas_vm.set_node_active("Process", self._node_c_active)
        print(f"[Test] Process node active: {self._node_c_active}")
    
    def _select_all(self):
        """Select all nodes."""
        for node in self.canvas_vm.get_nodes():
            self.canvas_vm.select_node(node.node_id, add_to_selection=True)
        print("[Test] Selected all nodes")
    
    def _clear_selection(self):
        """Clear selection."""
        self.canvas_vm.clear_selection()
        print("[Test] Cleared selection")
    
    def _update_status(self):
        """Update status label with current state."""
        selected = self.canvas_vm.get_selected_nodes()
        
        # Get undo/redo status
        undo_text = ""
        redo_text = ""
        if self.canvas_view.undo_stack:
            if self.canvas_view.undo_stack.canUndo():
                undo_text = f" | Undo: {self.canvas_view.undo_stack.undoText()}"
            if self.canvas_view.undo_stack.canRedo():
                redo_text = f" | Redo: {self.canvas_view.undo_stack.redoText()}"
        
        if selected:
            self.status_label.setText(f"Selected: {', '.join(selected)}{undo_text}{redo_text}")
            self.status_label.setStyleSheet("padding: 5px; background: #FFF9C4; border: 1px solid #FBC02D;")
        else:
            status_msg = f"Stage 3: Commands & Undo/Redo - Drag nodes, select, use Ctrl+Z/Ctrl+Shift+Z{undo_text}{redo_text}"
            self.status_label.setText(status_msg)
            self.status_label.setStyleSheet("padding: 5px; background: #E8F5E9; border: 1px solid #4CAF50;")


def main():
    """Run the test application."""
    if not HAS_PYQT:
        return
    
    app = QApplication(sys.argv)
    
    window = TestCanvasWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

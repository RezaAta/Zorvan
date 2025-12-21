# Moved from test_canvas_view.py — renamed to Examples/exp_canvas_view.py
# Purpose: Manual GUI test/demo for CanvasView. Moved out of test discovery paths.

#!/usr/bin/env python3
"""
CanvasView demo / manual test application. Use to visually test zoom, pan, drag, selection, and undo/redo.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )

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
        self.setWindowTitle("CanvasView Demo")
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
        self.status_label = QLabel("CanvasView Demo")
        self.status_label.setStyleSheet(
            "padding: 5px; background: #E8F5E9; border: 1px solid #4CAF50;"
        )
        main_layout.addWidget(self.status_label)

        # Add control buttons
        controls_layout = QHBoxLayout()

        undo_btn = QPushButton("Undo (Ctrl+Z)")
        undo_btn.clicked.connect(
            lambda: (
                self.canvas_view.undo_stack.undo()
                if self.canvas_view.undo_stack
                else None
            )
        )
        controls_layout.addWidget(undo_btn)

        redo_btn = QPushButton("Redo (Ctrl+Shift+Z)")
        redo_btn.clicked.connect(
            lambda: (
                self.canvas_view.undo_stack.redo()
                if self.canvas_view.undo_stack
                else None
            )
        )
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

        controls_layout.addStretch()

        main_layout.addLayout(controls_layout)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

        # Periodic status update
        from PyQt6.QtCore import QTimer

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(500)

    def _update_status(self):
        """Update status label with current state."""
        selected = self.canvas_vm.get_selected_nodes()
        if selected:
            self.status_label.setText(f"Selected: {', '.join(selected)}")
        else:
            self.status_label.setText("CanvasView Demo - No selection")


def main():
    """Run the demo application."""
    if not HAS_PYQT:
        return

    app = QApplication(sys.argv)

    window = TestCanvasWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

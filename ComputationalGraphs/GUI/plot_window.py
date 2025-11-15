"""Real-time plotting window for computational graph nodes."""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QCheckBox, QLabel, QSpinBox, QDialog, QListWidget,
                              QListWidgetItem, QDialogButtonBox, QComboBox)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class PlotConfigDialog(QDialog):
    """Dialog for configuring which nodes to plot."""
    
    def __init__(self, graph, default_max_iter=100, parent=None):
        super().__init__(parent)
        self.graph = graph
        self.setWindowTitle("Configure Plot")
        self.setModal(False)  # Non-blocking dialog
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        
        # Instructions
        instructions = QLabel("Select nodes to plot:")
        layout.addWidget(instructions)
        
        # Node list with checkboxes
        self.node_list = QListWidget()
        # Use NoSelection to prevent selection highlighting that causes cramping
        self.node_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        # Set spacing between items to prevent cramping
        self.node_list.setSpacing(2)
        
        # Add all nodes as checkable items
        for node in sorted(graph.nodes, key=lambda n: n.name):
            item = QListWidgetItem(node.name)
            item.setData(Qt.ItemDataRole.UserRole, node)  # Store node reference
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.node_list.addItem(item)
        
        layout.addWidget(self.node_list)
        
        # Max iterations
        iter_layout = QHBoxLayout()
        iter_layout.addWidget(QLabel("Max iterations:"))
        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setMinimum(10)
        self.max_iter_spin.setMaximum(100000)
        self.max_iter_spin.setValue(default_max_iter)  # Use provided default
        self.max_iter_spin.setSingleStep(10)
        iter_layout.addWidget(self.max_iter_spin)
        iter_layout.addStretch()
        layout.addLayout(iter_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_selected_nodes(self):
        """Get list of selected nodes."""
        selected = []
        for i in range(self.node_list.count()):
            item = self.node_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                node = item.data(Qt.ItemDataRole.UserRole)
                selected.append(node)
        return selected
    
    def get_max_iterations(self):
        """Get max iterations value."""
        return self.max_iter_spin.value()


class PlotWindow(QWidget):
    """Window for real-time plotting of node values."""
    
    def __init__(self, nodes, max_iterations, parent=None):
        super().__init__(parent)
        self.nodes = list(nodes)  # Keep as list to maintain order
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.parent_window = parent
        
        # Data storage: {node: [values]}
        self.data = {node: [] for node in nodes}
        self.iterations = []
        
        # Colors for different nodes
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                       '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        self.setup_ui()
        self.setup_plot()
    
    def setup_ui(self):
        """Setup the UI layout."""
        self.setWindowTitle("Node Values Plot")
        self.resize(900, 600)
        
        layout = QVBoxLayout()
        
        # Matplotlib canvas - give it maximum space
        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas, stretch=1)  # Stretch factor of 1 = takes all available space
        
        # Controls - compact layout at the bottom
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(5, 5, 5, 5)  # Minimal margins
        control_layout.setSpacing(8)  # Compact spacing
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_plot)
        self.clear_btn.setMaximumWidth(80)
        control_layout.addWidget(self.clear_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_node)
        self.remove_btn.setMaximumWidth(130)
        control_layout.addWidget(self.remove_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setMaximumWidth(80)
        control_layout.addWidget(self.close_btn)
        
        self.autoscale_check = QCheckBox("Auto-scale Y")
        self.autoscale_check.setChecked(True)
        control_layout.addWidget(self.autoscale_check)
        
        control_layout.addStretch()
        
        # Node list dropdown for removal
        self.node_combo = QComboBox()
        self.node_combo.setMaximumWidth(150)
        self.update_node_combo()
        control_layout.addWidget(QLabel("Remove:"))
        control_layout.addWidget(self.node_combo)
        
        self.iteration_label = QLabel("Iteration: 0 / {}".format(self.max_iterations))
        self.iteration_label.setMinimumWidth(150)
        control_layout.addWidget(self.iteration_label)
        
        layout.addLayout(control_layout, stretch=0)  # Stretch factor of 0 = use minimum space needed
        
        self.setLayout(layout)
    
    def update_node_combo(self):
        """Update the combo box with current nodes."""
        self.node_combo.clear()
        for node in self.nodes:
            self.node_combo.addItem(node.name, node)
    
    def remove_selected_node(self):
        """Remove the selected node from the plot."""
        if self.node_combo.count() == 0:
            return
        
        node = self.node_combo.currentData()
        if node in self.nodes:
            self.nodes.remove(node)
            
            # Remove line from plot
            if node in self.lines:
                self.lines[node].remove()
                del self.lines[node]
            
            # Remove data
            if node in self.data:
                del self.data[node]
            
            # Update combo box
            self.update_node_combo()
            
            # Redraw legend (only if there are nodes left)
            if self.nodes:
                self.ax.legend(loc='upper right')
            else:
                # Remove legend if no nodes left
                legend = self.ax.get_legend()
                if legend:
                    legend.remove()
            self.canvas.draw()
    
    def add_node(self, node):
        """Add a new node to the plot."""
        if node in self.nodes:
            return  # Already plotting this node
        
        self.nodes.append(node)
        self.data[node] = []
        
        # Add line for this node
        color = self.colors[len(self.nodes) % len(self.colors)]
        line, = self.ax.plot([], [], label=node.name, color=color, linewidth=2)
        self.lines[node] = line
        
        # Update combo box
        self.update_node_combo()
        
        # Redraw
        self.ax.legend(loc='upper right')
        self.canvas.draw()
    
    def setup_plot(self):
        """Setup the matplotlib plot."""
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('Iteration')
        self.ax.set_ylabel('Value')
        self.ax.set_title('Node Values Over Time')
        self.ax.grid(True, alpha=0.3)
        
        # Set initial x-axis limits
        self.ax.set_xlim(0, self.max_iterations)
        
        # Create line objects for each node
        self.lines = {}
        for i, node in enumerate(self.nodes):
            color = self.colors[i % len(self.colors)]
            line, = self.ax.plot([], [], label=node.name, color=color, linewidth=2)
            self.lines[node] = line
        
        # Only show legend if there are nodes
        if self.nodes:
            self.ax.legend(loc='upper right')
        self.canvas.draw()
    
    def update_plot(self, iteration):
        """Update plot with current node values."""
        self.current_iteration = iteration
        self.iteration_label.setText("Iteration: {} / {}".format(iteration, self.max_iterations))
        
        # Collect current values
        self.iterations.append(iteration)
        for node in self.nodes:
            value = node.value
            # Handle list/array values (take first element or compute mean)
            if isinstance(value, (list, tuple)):
                if len(value) > 0:
                    if isinstance(value[0], (int, float)):
                        value = np.mean(value)  # Average for numeric lists
                    else:
                        value = len(value)  # Count for non-numeric
                else:
                    value = 0
            elif value is None:
                value = 0
            
            self.data[node].append(float(value))
        
        # Update line data
        for node in self.nodes:
            self.lines[node].set_data(self.iterations, self.data[node])
        
        # Auto-scale Y axis if enabled
        if self.autoscale_check.isChecked():
            # Get all values to determine Y limits
            all_values = []
            for values in self.data.values():
                all_values.extend(values)
            
            if all_values:
                y_min = min(all_values)
                y_max = max(all_values)
                # Add 10% padding
                y_range = y_max - y_min
                if y_range == 0:
                    y_range = 1
                self.ax.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)
        
        # Adjust X axis if we exceed max iterations
        if iteration > self.max_iterations:
            self.ax.set_xlim(0, iteration + 10)
        
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear all plot data."""
        self.current_iteration = 0
        self.iterations = []
        for node in self.nodes:
            self.data[node] = []
            self.lines[node].set_data([], [])
        
        self.ax.set_xlim(0, self.max_iterations)
        self.iteration_label.setText("Iteration: 0 / {}".format(self.max_iterations))
        self.canvas.draw()
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up matplotlib resources
        self.figure.clear()
        event.accept()

"""PyQtGraph-based plotting window for computational graph nodes."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QComboBox, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QToolTip
import pyqtgraph as pg
pg.setConfigOptions(antialias=True)  # Enable antialiasing globally for crisp lines
import numpy as np


class PlotWindowPG(QWidget):
    """A simple PyQtGraph equivalent of PlotWindow.

    Provides the same public interface as the Matplotlib-based PlotWindow so it
    can be used interchangeably: add_node, remove_selected_node, update_plot, clear_plot.
    """

    def __init__(self, nodes, max_iterations, parent=None):
        super().__init__(parent)
        self.nodes = list(nodes)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.backend = 'pyqtgraph'

        # Data storage: {node: [values]}
        self.data = {node: [] for node in nodes}

        # Colors
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                       '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        self._setup_ui()
        self._setup_plot()

    def _setup_ui(self):
        self.setWindowTitle('Node Values Plot (pyqtgraph)')
        self.resize(900, 600)
        layout = QVBoxLayout()

        self.plot_widget = pg.PlotWidget()
        # Use white background for better visibility
        try:
            self.plot_widget.setBackground('w')
        except Exception:
            try:
                self.plot_widget.setBackground((255, 255, 255))
            except Exception:
                pass
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('bottom', 'Iteration')
        self.plot_widget.setLabel('left', 'Value')
        layout.addWidget(self.plot_widget)

        # Control buttons
        control_layout = QHBoxLayout()
        self.clear_btn = QPushButton('Clear')
        self.clear_btn.clicked.connect(self.clear_plot)
        control_layout.addWidget(self.clear_btn)

        self.remove_btn = QPushButton('Remove Selected')
        self.remove_btn.clicked.connect(self.remove_selected_node)
        control_layout.addWidget(self.remove_btn)

        self.autoscale_check = QCheckBox('Auto-scale Y')
        self.autoscale_check.setChecked(True)
        control_layout.addWidget(self.autoscale_check)

        self.reset_zoom_btn = QPushButton('Reset Zoom')
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        control_layout.addWidget(self.reset_zoom_btn)

        self.pause_plot_check = QCheckBox('Pause Plot')
        self.pause_plot_check.setChecked(False)
        control_layout.addWidget(self.pause_plot_check)

        control_layout.addStretch()

        self.node_combo = QComboBox()
        # Create visibility list early so update_node_combo can safely populate it
        self.visibility_list = QListWidget()
        self.visibility_list.setMaximumHeight(120)
        self.visibility_list.setSpacing(2)
        self.visibility_list.itemChanged.connect(self._on_visibility_changed)
        self.update_node_combo()
        self.node_combo.setMaximumWidth(200)
        control_layout.addWidget(QLabel('Remove:'))
        control_layout.addWidget(self.node_combo)

        self.iteration_label = QLabel(f'Iteration: 0 / {self.max_iterations}')
        self.iteration_label.setMinimumWidth(150)
        control_layout.addWidget(self.iteration_label)

        layout.addLayout(control_layout)
        self.setLayout(layout)

        # Visibility list label and widget (created earlier but added to layout now)
        # Populate with any nodes created so far
        self._populate_visibility_list()
        layout.addWidget(QLabel('Plotted Nodes:'))
        layout.addWidget(self.visibility_list)

    def _populate_visibility_list(self):
        self.visibility_list.clear()
        for node in self.nodes:
            item = QListWidgetItem(node.name)
            item.setData(Qt.ItemDataRole.UserRole, node)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.visibility_list.addItem(item)

    def _on_visibility_changed(self, item: QListWidgetItem):
        node = item.data(Qt.ItemDataRole.UserRole)
        visible = item.checkState() == Qt.CheckState.Checked
        if node in self.curves:
            self.curves[node].setVisible(visible)

    def _setup_plot(self):
        self.curves = {}
        for i, node in enumerate(self.nodes):
            pen = pg.mkPen(color=self.colors[i % len(self.colors)], width=2)
            curve = self.plot_widget.plot([], [], pen=pen, name=node.name)
            self.curves[node] = curve

        # Legend
        # Legend - add unique items for each curve
        self.legend = self.plot_widget.addLegend()
        # Add legend items, avoid duplicates
        try:
            existing_names = []
            for (sample, label) in getattr(self.legend, 'items', []):
                try:
                    existing_names.append(label.text)
                except Exception:
                    try:
                        existing_names.append(str(label))
                    except Exception:
                        pass
        except Exception:
            existing_names = []
        for node, curve in self.curves.items():
            # Generate a unique label if there are duplicates already in legend
            try:
                unique_label = self._generate_unique_legend_label(node.name, existing_names)
                self.legend.addItem(curve, unique_label)
            except Exception:
                pass

        # Enable mouse interactions (pan/zoom)
        self.plot_widget.setMouseEnabled(x=True, y=True)

        # Signal proxy to handle hover updates
        try:
            self._mouse_proxy = pg.SignalProxy(self.plot_widget.scene().sigMouseMoved, rateLimit=60, slot=self._on_mouse_moved)
        except Exception:
            self._mouse_proxy = None

    def _generate_unique_legend_label(self, base_label, existing_names):
        """Return a unique label based on base_label, modifying existing_names in-place.

        The function appends the new/unique label to existing_names so callers don't need
        to append it themselves. A minimal-friendly suffix format is used: ' (N)'.
        """
        try:
            if base_label not in existing_names:
                existing_names.append(base_label)
                return base_label
            # If base exists, find smallest positive integer suffix not used
            suffix = 1
            while True:
                candidate = f"{base_label} ({suffix})"
                if candidate not in existing_names:
                    existing_names.append(candidate)
                    return candidate
                suffix += 1
        except Exception:
            # Fallback: return base_label even in case of unexpected errors
            return base_label

    def update_node_combo(self):
        self.node_combo.clear()
        for node in self.nodes:
            self.node_combo.addItem(node.name, node)
        # Keep the visibility list in sync as well
        self._populate_visibility_list()

    def add_node(self, node):
        if node in self.nodes or node in self.curves:
            return
        self.nodes.append(node)
        self.data[node] = []
        pen = pg.mkPen(color=self.colors[len(self.nodes) % len(self.colors)], width=2)
        curve = self.plot_widget.plot([], [], pen=pen, name=node.name)
        self.curves[node] = curve
        # Add legend entry only if name not present
        try:
            existing_names = [label.text for (sample, label) in getattr(self.legend, 'items', []) if hasattr(label, 'text')]
        except Exception:
            existing_names = []
        try:
            unique_label = self._generate_unique_legend_label(node.name, existing_names)
            self.legend.addItem(curve, unique_label)
        except Exception:
            pass
        self.update_node_combo()
        self._populate_visibility_list()

    def remove_selected_node(self):
        if self.node_combo.count() == 0:
            return
        node = self.node_combo.currentData()
        if node in self.nodes:
            self.nodes.remove(node)
            # Remove curve
            if node in self.curves:
                try:
                    self.plot_widget.removeItem(self.curves[node])
                except Exception:
                    pass
                del self.curves[node]
            if node in self.data:
                del self.data[node]
            self.update_node_combo()
            self._populate_visibility_list()
            # Rebuild legend to avoid stale/duplicate entries
            try:
                # Remove existing legend and recreate
                try:
                    self.plot_widget.removeItem(self.legend)
                except Exception:
                    pass
                self.legend = self.plot_widget.addLegend()
                existing_names = []
                for n, c in self.curves.items():
                    try:
                            unique_label = self._generate_unique_legend_label(n.name, existing_names)
                            self.legend.addItem(c, unique_label)
                    except Exception:
                        pass
            except Exception:
                pass

    def update_plot(self, iteration):
        if self.pause_plot_check.isChecked():
            return
        self.current_iteration = iteration
        self.iteration_label.setText(f'Iteration: {iteration} / {self.max_iterations}')
        # Append iteration to data and update curves
        for node in self.nodes:
            value = node.value
            if isinstance(value, (list, tuple)):
                if len(value) > 0 and isinstance(value[0], (int, float)):
                    value = np.mean(value)
                else:
                    value = len(value) if value else 0
            elif value is None:
                value = 0
            try:
                self.data[node].append(float(value))
            except Exception:
                # fallback
                self.data[node].append(0.0)

        for node, curve in self.curves.items():
            ys = self.data.get(node, [])
            xs = list(range(len(ys)))
            # Use antialiasing for smoother lines
            try:
                curve.setData(xs, ys, antialias=True)
            except Exception:
                curve.setData(xs, ys)

        if self.autoscale_check.isChecked():
            # Determine y range
            all_values = []
            for v in self.data.values():
                all_values.extend(v)
            if all_values:
                y_min = min(all_values)
                y_max = max(all_values)
                if y_min == y_max:
                    y_min -= 0.5
                    y_max += 0.5
                self.plot_widget.setYRange(y_min - 0.1 * (y_max - y_min), y_max + 0.1 * (y_max - y_min))

    def reset_zoom(self):
        # Reset X range based on iterations and auto-range Y
        self.plot_widget.setXRange(0, max(self.max_iterations, self.current_iteration))
        if not self.autoscale_check.isChecked():
            # If autoscale not enabled, attempt to set Y range to default
            self.plot_widget.setYRange(-1, 1)

    def _on_mouse_moved(self, evt):
        try:
            pos = evt[0]  # event is a tuple from SignalProxy (scene coords)
            vb = self.plot_widget.getPlotItem().vb
            mousePoint = vb.mapSceneToView(pos)
            x_view = mousePoint.x()
            if x_view is None:
                return

            # Threshold in pixels
            PIXEL_THRESHOLD = 10.0

            best = {
                'node': None,
                'idx': None,
                'y': None,
                'dist': float('inf')
            }

            for node, ys in self.data.items():
                try:
                    # Skip empty data series
                    if not ys:
                        continue
                    # Skip hidden curves
                    try:
                        curve = self.curves.get(node, None)
                        if curve is not None and not curve.isVisible():
                            continue
                    except Exception:
                        # continue even if visibility check fails
                        pass

                    # Use array math to find closest x index to the mouse x position
                    ys_arr = np.array(ys, dtype=float)
                    xs_arr = np.arange(len(ys_arr))
                    # Find the index with minimum absolute difference from the mouse X
                    rel_idx = int(np.abs(xs_arr - x_view).argmin())
                    y_val = float(ys_arr[rel_idx])

                    # Map the view/data coordinates (rel_idx, y_val) to scene coordinates
                    try:
                        scene_pt = vb.mapViewToScene(pg.Point(rel_idx, y_val))
                    except Exception:
                        # Map using explicit QPointF fallback
                        try:
                            scene_pt = vb.mapViewToScene(pg.QtCore.QPointF(rel_idx, y_val))
                        except Exception:
                            # If mapping fails, skip this series
                            continue

                    # Compute pixel distance in scene coordinates between cursor and this data point
                    dx = scene_pt.x() - pos.x()
                    dy = scene_pt.y() - pos.y()
                    dist = (dx * dx + dy * dy) ** 0.5

                    if dist < best['dist']:
                        best.update({
                            'node': node,
                            'idx': rel_idx,
                            'y': y_val,
                            'dist': dist
                        })
                except Exception:
                    # Ignore errors for individual series to avoid breaking the hover
                    continue

            # If we found a nearest series within the pixel threshold - show that tooltip only
            if best['node'] is not None and best['dist'] < PIXEL_THRESHOLD:
                try:
                    tooltip = f"{best['node'].name}: {best['y']:.4f}"
                    QToolTip.showText(QCursor.pos(), tooltip)
                except Exception:
                    # If tooltip display fails for some reason, ensure we hide any text
                    try:
                        QToolTip.hideText()
                    except Exception:
                        pass
            else:
                # Hide tooltip if nothing is sufficiently near
                try:
                    QToolTip.hideText()
                except Exception:
                    pass
        except Exception:
            # Defensively swallow all exceptions to avoid breaking the UI
            pass

    def clear_plot(self):
        self.current_iteration = 0
        self.iteration_label.setText(f'Iteration: 0 / {self.max_iterations}')
        for node in list(self.nodes):
            self.data[node] = []
            if node in self.curves:
                self.curves[node].setData([], [])

    def closeEvent(self, event):
        # Clean up
        try:
            self.plot_widget.clear()
        except Exception:
            pass
        event.accept()

"""PlotView: PyQt6 view bound to PlotViewModel (Matplotlib backend).

This view listens to PlotViewModel observable properties and updates the
matplotlib canvas accordingly. It is intentionally lightweight and testable
in headless environments using the 'offscreen' platform.
"""

from typing import Dict

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QVBoxLayout, QWidget


class PlotView(QWidget):
    """Widget view that binds to a PlotViewModel instance.

    Expects a PlotViewModel implementing the API used in gui_framework.viewmodels.plot_viewmodel.
    """

    def __init__(self, viewmodel, parent=None):
        super().__init__(parent)
        self._vm = viewmodel
        self._lines: Dict[str, object] = {}

        self.figure = Figure(figsize=(6, 4), facecolor="white")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel("Iteration")
        self.ax.set_ylabel("Value")
        self.ax.grid(True, alpha=0.3)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        # Initialize lines for existing nodes
        for name in self._vm.get_plotted_nodes():
            self._create_line(name)

        # Bind to viewmodel observables
        self._vm.observe_property("nodes_changed", self._on_nodes_changed)
        self._vm.observe_property("data_updated", self._on_data_updated)
        self._vm.observe_property("backend_changed", self._on_backend_changed)

        # Initial draw
        self.update_plot()

    def _create_line(self, node_name: str):
        if node_name in self._lines:
            return
        color = self._vm.get_node_color(node_name) or "#1f77b4"
        (line,) = self.ax.plot([], [], label=node_name, color=color, linewidth=2)
        self._lines[node_name] = line
        if self._lines:
            self.ax.legend(loc="upper right")

    def _remove_line(self, node_name: str):
        if node_name not in self._lines:
            return
        line = self._lines.pop(node_name)
        try:
            line.remove()
        except Exception:
            pass
        # Recreate legend to ensure labels remain unique
        legend = self.ax.get_legend()
        if legend:
            legend.remove()
        if self._lines:
            self.ax.legend(loc="upper right")

    def _on_nodes_changed(self, old, new):
        # Sync nodes based on ViewModel state
        current = set(self._vm.get_plotted_nodes())
        existing = set(self._lines.keys())
        # Add new
        for name in sorted(current - existing):
            self._create_line(name)
        # Remove missing
        for name in sorted(existing - current):
            self._remove_line(name)
        self.update_plot()

    def _on_data_updated(self, old, new):
        # Update plot data from ViewModel
        self.update_plot()

    def _on_backend_changed(self, old, new):
        # For now we only support matplotlib - ignore other backends
        pass

    def update_plot(self):
        all_data = self._vm.get_all_plot_data()
        # Update each line's data
        for name, line in list(self._lines.items()):
            points = all_data.get(name, [])
            iterations = [p.iteration for p in points]
            values = [p.value for p in points]
            try:
                line.set_data(iterations, values)
            except Exception:
                pass

        # Adjust axes
        min_iter, max_iter = self._vm.get_iteration_range()
        if max_iter == 0:
            self.ax.set_xlim(0, self._vm.get_max_iterations())
        else:
            self.ax.set_xlim(
                max(0, min_iter), max(max_iter, self._vm.get_max_iterations())
            )

        # Auto-scale Y
        # Compute overall value range
        min_y, max_y = None, None
        for name in self._lines.keys():
            vr = self._vm.get_value_range(name)
            if vr:
                if min_y is None or vr[0] < min_y:
                    min_y = vr[0]
                if max_y is None or vr[1] > max_y:
                    max_y = vr[1]
        if min_y is not None and max_y is not None:
            if min_y == max_y:
                self.ax.set_ylim(min_y - 1, max_y + 1)
            else:
                padding = 0.1 * (max_y - min_y)
                self.ax.set_ylim(min_y - padding, max_y + padding)

        self.canvas.draw_idle()

    def cleanup(self):
        # Unbind observers
        try:
            self._vm.unobserve_property("nodes_changed", self._on_nodes_changed)
            self._vm.unobserve_property("data_updated", self._on_data_updated)
            self._vm.unobserve_property("backend_changed", self._on_backend_changed)
        except Exception:
            pass
        # Clear figure
        try:
            self.figure.clear()
        except Exception:
            pass


def create_plot_view(viewmodel, parent=None):
    return PlotView(viewmodel, parent)

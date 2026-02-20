"""Dialog for generating MLP graphs."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from zorvan.Core.Graph import Graph
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Nodes.LinearNode import LinearNode
from zorvan.Nodes.ReLUNode import ReLUNode
from zorvan.Nodes.SigmoidNode import SigmoidNode
from zorvan.Nodes.TanhNode import TanhNode

"""
Thin adapter that exposes the MVVM `MLPGeneratorDialog` under the legacy import path.
This keeps existing code that imports `zorvan.GUI.MLPGeneratorDialog` working
while we migrate to the MVVM implementation in `gui_framework.views.dialogs`.
"""

try:
    from gui_framework.views.dialogs.mlp_generator_dialog import (
        MLPGeneratorDialog as MVVMMlpDialog,
    )
except Exception as e:
    raise ImportError("MVVM MLPGeneratorDialog not available: " + str(e))


class MLPGeneratorDialog:
    """Legacy-compatible adapter around the MVVM dialog.

    This adapter retains legacy method names and helper functions that older
    tests and code expect while delegating to the new MVVM dialog for actual
    UI and generation logic.
    """

    _activation_map = {
        "Tanh": TanhNode,
        "Sigmoid": SigmoidNode,
        "ReLU": ReLUNode,
        "Linear": LinearNode,
    }

    def __init__(self, parent=None):
        self._dlg = MVVMMlpDialog(parent)

    def exec(self):
        return self._dlg.exec()

    def get_graph(self):
        g = self._dlg.get_graph()
        if g is None:
            return None

        # If the viewmodel returned activation *names*, also expose the
        # legacy attribute `hiddenActivationFunctions` as a list of node classes
        if hasattr(g, "hiddenLayerActivations"):
            try:
                g.hiddenActivationFunctions = [
                    self._get_activation_class(name)
                    for name in g.hiddenLayerActivations
                ]
            except Exception:
                g.hiddenActivationFunctions = []

        # If the returned object is already a core Graph, return it
        try:
            from zorvan.Core.Graph import Graph as CoreGraph
        except Exception:
            CoreGraph = None

        if CoreGraph is not None and isinstance(g, CoreGraph):
            return g

        # Otherwise convert the light-weight graph returned by the VM into a
        # full-fledged Core.Graph so the rest of the application can operate
        # on it (AddNode, ConnectPreNode, UpdateAdjacencyMatrix etc.).
        if CoreGraph is None:
            # Can't do conversion without core Graph class; return original
            return g

        core_g = CoreGraph(name=getattr(g, "graph_name", "Generated MLP"))

        # Create placeholder BasicNode subclass for generated nodes
        from zorvan.Nodes.BasicNode import BasicNode

        class PlaceholderNode(BasicNode):
            def __init__(self, name):
                super().__init__(name)

            def Operation(self, *inputs):
                # Minimal operation - return 0 or sum; not used until user wires real nodes
                try:
                    return sum(inputs) if inputs else 0
                except Exception:
                    return 0

            def IsValidInput(self, inp):
                return True

        # Map old nodes to new placeholder instances
        old_to_new = {}
        for old_node in getattr(g, "nodes", []):
            new_node = PlaceholderNode(getattr(old_node, "name", ""))
            # Copy commonly used attributes
            for attr in [
                "value",
                "data",
                "gui_pos",
                "gui_color",
                "gui_radius",
                "gui_label",
                "gui_label_color",
            ]:
                try:
                    if hasattr(old_node, attr):
                        setattr(new_node, attr, getattr(old_node, attr))
                except Exception:
                    pass
            core_g.AddNode(new_node)
            old_to_new[old_node] = new_node

        # Recreate predecessor links
        for old_node in getattr(g, "nodes", []):
            new_node = old_to_new.get(old_node)
            if new_node is None:
                continue
            preds = getattr(old_node, "predecessors", []) or []
            for p in preds:
                new_pred = old_to_new.get(p)
                if new_pred is not None:
                    try:
                        core_g.ConnectPreNode(new_node, new_pred)
                    except Exception:
                        try:
                            new_node.AddPreNode(new_pred)
                        except Exception:
                            pass

        # Copy compatibility attributes
        for attr in ["hiddenLayerSizes", "hiddenLayerActivations", "bias", "hasBias"]:
            try:
                if hasattr(g, attr):
                    setattr(core_g, attr, getattr(g, attr))
            except Exception:
                pass

        # Rebuild adjacency matrix to ensure consistency
        try:
            core_g.UpdateAdjacencyMatrix()
        except Exception:
            pass

        return core_g

    def close(self):
        return self._dlg.close()

    def _get_activation_class(self, name: str):
        """Compatibility helper: map activation name -> Node class."""
        return self._activation_map.get(name)

    # Legacy-compatible method names used by tests
    def _update_hidden_layer_sizes(self, count: int):
        return self._dlg._update_hidden_sizes(count)

    def _toggle_per_layer_selectors(self, count: int):
        # Turn on the per-layer checkbox and ensure underlying widgets are updated
        try:
            self._dlg.per_layer_checkbox.setChecked(True)
            return self._dlg._toggle_per_layer_selectors(count)
        except Exception:
            return None

    def _generate_mlp(self):
        # Delegate to MVVM generate trigger
        try:
            return self._dlg._on_generate()
        except Exception:
            # fallback: try exec
            return self._dlg.exec()

    @property
    def hidden_layer_spinboxes(self):
        # Expose old name used by tests
        return getattr(self._dlg, "_hidden_spinboxes", [])

    @property
    def per_layer_selectors(self):
        # Legacy name used in some tests; map to the internal per-layer combos
        return getattr(self._dlg, "_per_layer_combos", [])

    def __getattr__(self, name):
        return getattr(self._dlg, name)

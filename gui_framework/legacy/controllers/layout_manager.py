"""
Layout Manager - handles graph layout algorithms.

Extracted from graph_canvas.py to reduce complexity and improve maintainability.
This module provides layout algorithms for positioning nodes on the canvas.
"""

import re
from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

from PyQt6.QtGui import QColor


class LayoutManager:
    """Manages graph layout algorithms and node positioning.

    This class encapsulates layout computation logic that was previously
    embedded in GraphCanvas.
    """

    def __init__(self, canvas=None):
        """Initialize the layout manager.

        Args:
            canvas: Reference to the GraphCanvas (optional, for grid settings)
        """
        self.canvas = canvas

    @property
    def grid_size(self) -> int:
        """Get grid size from canvas or use default."""
        if self.canvas and hasattr(self.canvas, "grid_size"):
            return self.canvas.grid_size
        return 20

    @property
    def snap_step(self) -> int:
        """Get snap step from canvas or use default."""
        if self.canvas and hasattr(self.canvas, "snap_step"):
            return self.canvas.snap_step
        return 4

    @property
    def snap_to_grid(self) -> bool:
        """Check if snap to grid is enabled."""
        if self.canvas and hasattr(self.canvas, "snap_to_grid"):
            return self.canvas.snap_to_grid
        return False

    def snap_point(
        self, x: float, y: float, step: Optional[int] = None
    ) -> Tuple[float, float]:
        """Snap a point to the grid.

        Args:
            x: X coordinate
            y: Y coordinate
            step: Optional step size override

        Returns:
            Tuple of snapped (x, y) coordinates
        """
        if not self.snap_to_grid or self.grid_size <= 0:
            return x, y

        try:
            s = int(step or self.snap_step)
            unit = self.grid_size * s
            sx = round(x / unit) * unit
            sy = round(y / unit) * unit
            return sx, sy
        except Exception:
            return x, y

    def compute_positions(
        self, node_items: Dict[Any, Any], layout_type: str = "ann"
    ) -> Dict[Any, Tuple[float, float]]:
        """Compute positions for all nodes based on layout type.

        Args:
            node_items: Dictionary mapping node objects to NodeItem widgets
            layout_type: Layout algorithm to use ('ann', 'spring', 'good', etc.)

        Returns:
            Dictionary mapping node objects to (x, y) positions
        """
        if not node_items:
            return {}

        pos = {}

        # Use existing GUI positions as fallback
        for node, item in node_items.items():
            try:
                if hasattr(node, "gui_pos") and node.gui_pos is not None:
                    if (
                        isinstance(node.gui_pos, (tuple, list))
                        and len(node.gui_pos) >= 2
                    ):
                        pos[node] = (float(node.gui_pos[0]), float(node.gui_pos[1]))
                    else:
                        pos[node] = (float(item.pos().x()), float(item.pos().y()))
                else:
                    pos[node] = (float(item.pos().x()), float(item.pos().y()))
            except Exception:
                pos[node] = (0.0, 0.0)

        return pos

    def compute_ann_layout(
        self, nodes, scale: float = 300
    ) -> Dict[Any, Tuple[float, float]]:
        """Compute ANN-style layout positions.

        Returns a mapping of nodes to their existing GUI positions if available,
        else returns (0.0, 0.0) default positions.

        Args:
            nodes: Iterable of node objects
            scale: Scale factor for layout

        Returns:
            Dictionary mapping nodes to (x, y) positions
        """
        pos = {}
        for node in nodes:
            if hasattr(node, "gui_pos") and node.gui_pos is not None:
                pos[node] = tuple(node.gui_pos)
            else:
                pos[node] = (0.0, 0.0)
        return pos

    def compute_good_layout(
        self, nodes, node_names: Dict[Any, str], scale: float = 300
    ) -> Dict[Any, Tuple[float, float]]:
        """Compute the 'Good' MLP layout using a cellular grid.

        Uses a cellular grid where each cell is the node size plus padding.
        Lays out nodes deterministically left-to-right through:
        input -> buffers -> weights -> mults -> additions -> activations -> buffer.

        Args:
            nodes: Iterable of node objects
            node_names: Dictionary mapping nodes to their names
            scale: Scale factor for layout

        Returns:
            Dictionary mapping nodes to (x, y) positions
        """
        # Categorize nodes by pattern
        inputs = []
        buffs_x = {}
        weights = defaultdict(list)
        muls = []
        adds = defaultdict(list)
        acts = defaultdict(list)
        buffs_h = defaultdict(list)
        derivatives = []
        outputs_add = []
        outputs_act = []

        for node in nodes:
            name = node_names.get(node, "")
            self._categorize_node(
                node,
                name,
                inputs,
                buffs_x,
                weights,
                muls,
                adds,
                acts,
                buffs_h,
                derivatives,
                outputs_add,
                outputs_act,
            )

        # Compute grid dimensions
        step_per_layer = 8
        num_hidden_layers = max(adds.keys()) + 1 if adds else 0
        _max_hidden_neurons = (
            max(
                (max([n for (_, n) in nodes_list]) + 1) if nodes_list else 0
                for nodes_list in adds.values()
            )
            if adds
            else 0
        )

        # Cell size
        grid_unit = self.grid_size * self.snap_step
        cell_w = grid_unit
        cell_h = grid_unit

        def cell_to_pixel(col, row):
            x = col * cell_w
            y = row * cell_h
            if self.snap_to_grid:
                x, y = self.snap_point(x, y)
            return (x, y)

        pos = {}

        # Place inputs and input buffers
        for node, idx in inputs:
            row = idx
            pos[node] = cell_to_pixel(0, row)
            buff = buffs_x.get(idx)
            if buff:
                buff_row = row - 1 if row > 0 else row + 1
                pos[buff] = cell_to_pixel(1, buff_row)

        # Hidden layer placements
        for layer, nodes_list in adds.items():
            for node, n in nodes_list:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 2, n)

        for layer, nodes_list in acts.items():
            for node, n in nodes_list:
                base = 2 + (layer * step_per_layer)
                pos[node] = cell_to_pixel(base + 3, n)

        for layer, nodes_list in buffs_h.items():
            for node, n in nodes_list:
                base = 2 + (layer * step_per_layer)
                buff_row = n - 1 if n > 0 else n + 1
                pos[node] = cell_to_pixel(base + 4, buff_row)

        # Weights placement with diagonal distribution
        weight_row_map = {}
        weight_col_map = {}

        for key, wlist in weights.items():
            grouped_by_j = defaultdict(list)
            for node, i, j in wlist:
                grouped_by_j[j].append((node, i, j))

            for j, items in grouped_by_j.items():
                items_sorted = sorted(items, key=lambda x: x[1])
                c = len(items_sorted)
                start_row = j - (c - 1) // 2

                for idx_in_group, (node, i, j2) in enumerate(items_sorted):
                    row = start_row + idx_in_group
                    target_layer = key[0] if isinstance(key[0], int) else 0
                    base = (
                        2 + ((max(0, target_layer - 1)) * step_per_layer)
                        if target_layer > 0
                        else 2
                    )
                    col = base + j
                    pos[node] = cell_to_pixel(col, row)
                    weight_row_map[node] = row
                    weight_col_map[node] = col

        # Multiplications placement
        for node in muls:
            name = node_names.get(node, "")
            self._place_multiplication_node(
                node,
                name,
                pos,
                weights,
                weight_row_map,
                weight_col_map,
                step_per_layer,
                cell_to_pixel,
            )

        # Output positions
        last_group_base = 2 + (num_hidden_layers * step_per_layer)
        for node, idx in outputs_add:
            pos[node] = cell_to_pixel(last_group_base + 2, idx)
        for node, idx in outputs_act:
            pos[node] = cell_to_pixel(last_group_base + 3, idx)

        # Derivatives
        for node, layer, n in derivatives:
            if layer == "y":
                col = last_group_base + 4
                row = n
            else:
                base = 2 + (layer * step_per_layer)
                col = base + 5
                row = n + 1
            pos[node] = cell_to_pixel(col, row)

        return pos

    def _categorize_node(
        self,
        node,
        name,
        inputs,
        buffs_x,
        weights,
        muls,
        adds,
        acts,
        buffs_h,
        derivatives,
        outputs_add,
        outputs_act,
    ):
        """Categorize a node by its name pattern."""
        # Input nodes
        m = re.match(r"^x(\d+)$", name)
        if m:
            inputs.append((node, int(m.group(1))))
            return

        # Input buffers
        m = re.match(r"^Buff_x(\d+)$", name)
        if m:
            buffs_x[int(m.group(1))] = node
            return

        # First layer weights
        m = re.match(r"^W_x(\d+)H(\d+)N(\d+)$", name)
        if m:
            i = int(m.group(1))
            layer = int(m.group(2))
            j = int(m.group(3))
            weights[(layer, f"x{i}")].append((node, i, j))
            return

        # Hidden-to-hidden weights
        m = re.match(r"^W_H(\d+)N(\d+)H(\d+)N(\d+)$", name)
        if m:
            from_layer = int(m.group(1))
            i = int(m.group(2))
            to_l = int(m.group(3))
            j = int(m.group(4))
            weights[(to_l, f"H{from_layer}")].append((node, i, j))
            return

        # Multiplication nodes
        m = re.match(r"^Mul_([A-Za-z].+)$", name)
        if m:
            muls.append(node)
            return

        # Addition nodes
        m = re.match(r"^Add_(?:L|H)(\d+)N(\d+)$", name)
        if m:
            layer = int(m.group(1))
            n = int(m.group(2))
            adds[layer].append((node, n))
            return

        # Activation nodes
        m = re.match(r"^Act_(?:L|H)(\d+)N(\d+)$", name)
        if m:
            layer = int(m.group(1))
            n = int(m.group(2))
            acts[layer].append((node, n))
            return

        # Hidden buffers
        m = re.match(r"^Buff_H(\d+)N(\d+)$", name)
        if m:
            layer = int(m.group(1))
            n = int(m.group(2))
            buffs_h[layer].append((node, n))
            return

        # Derivatives
        m = re.match(r"^D_H(\d+)N(\d+)$", name)
        if m:
            layer = int(m.group(1))
            n = int(m.group(2))
            derivatives.append((node, layer, n))
            return

        m = re.match(r"^D_y(\d+)$", name)
        if m:
            derivatives.append((node, "y", int(m.group(1))))
            return

        # Output additions
        m = re.match(r"^Add_y(\d+)$", name)
        if m:
            outputs_add.append((node, int(m.group(1))))
            return

        # Output activations
        m = re.match(r"^y(\d+)$", name)
        if m:
            outputs_act.append((node, int(m.group(1))))
            return

    def _place_multiplication_node(
        self,
        node,
        name,
        pos,
        weights,
        weight_row_map,
        weight_col_map,
        step_per_layer,
        cell_to_pixel,
    ):
        """Place a multiplication node based on its pattern."""
        # First layer multiplications
        m = re.match(r"^Mul_x(\d+)H(\d+)$", name)
        if m:
            i = int(m.group(1))
            j = int(m.group(2))
            assigned_row = None
            assigned_col = None

            if (0, "x") in weights:
                for wn, si, sj in weights[(0, "x")]:
                    if si == i and sj == j:
                        assigned_row = weight_row_map.get(wn)
                        assigned_col = weight_col_map.get(wn)
                        break

            row = assigned_row if assigned_row is not None else j
            col = (assigned_col + 1) if assigned_col is not None else 3
            pos[node] = cell_to_pixel(col, row)
            return

        # Hidden-to-hidden multiplications
        m = re.match(r"^Mul_H(\d+)N(\d+)H(\d+)N(\d+)$", name)
        if m:
            to_l = int(m.group(3))
            j = int(m.group(4))
            i = int(m.group(2))
            assigned_row = None
            assigned_col = None

            key = (to_l, f"H{to_l-1}")
            if key in weights:
                for wn, si, sj in weights[key]:
                    if si == i and sj == j:
                        assigned_row = weight_row_map.get(wn)
                        assigned_col = weight_col_map.get(wn)
                        break

            base = 2 + ((to_l - 1) * step_per_layer)
            row = assigned_row if assigned_row is not None else j
            col = (assigned_col + 1) if assigned_col is not None else base + 1
            pos[node] = cell_to_pixel(col, row)
            return

        # Output multiplications
        m = re.match(r"^Mul_H(\d+)N(\d+)y(\d+)$", name)
        if m:
            from_l = int(m.group(1))
            j = int(m.group(3))
            base = 2 + (from_l * step_per_layer)
            pos[node] = cell_to_pixel(base + 1, j)
            return

        # Fallback
        pos[node] = cell_to_pixel(3, 0)


class NodeColorizer:
    """Handles ANN-specific node coloring."""

    # Color scheme constants
    COLOR_INPUT = QColor(100, 100, 100)  # Dark gray
    COLOR_LABEL = QColor(180, 60, 60)  # Dark red
    COLOR_WEIGHT = QColor(60, 100, 180)  # Dark blue
    COLOR_BUFFER = QColor(200, 149, 62)  # Yellow/Gold
    COLOR_DERIVATIVE = QColor(60, 150, 60)  # Dark green
    COLOR_GRADIENT = QColor(120, 80, 150)  # Dark purple
    COLOR_DEFAULT = QColor(100, 100, 100)  # Dark gray

    @classmethod
    def get_node_color(cls, name: str) -> QColor:
        """Determine the appropriate color for a node based on its name.

        Color scheme:
        - Gray: Input streams, activations, additions, multiplication (forward pass)
        - Blue: Weights (W_*, wn_*, wx_*), LR, dW nodes
        - Green: Activation derivatives (D_*, *derivative)
        - Red: Label streams, Error nodes
        - Purple: Backprop gradient nodes (EG_*, LRMult_*, WGS_*)
        - Yellow/Gold: Buffer nodes

        Args:
            name: Node name

        Returns:
            QColor for the node
        """
        # Red: Label streams and Error nodes
        if (
            name.startswith("Label_")
            or name.startswith("yd")
            or name.startswith("Error_")
            or (name.startswith("e") and "E" in name)
        ):
            return cls.COLOR_LABEL

        # Blue: Weights, LR, dW nodes
        if (
            name.startswith("W_")
            or name.startswith("wn")
            or name.startswith("wx")
            or name == "LearningRate"
            or name == "LR"
            or name.startswith("dW_")
        ):
            return cls.COLOR_WEIGHT

        # Yellow/Gold: Buffer nodes
        if "Buff" in name or "Buffer" in name or "buffer" in name:
            return cls.COLOR_BUFFER

        # Green: Activation derivatives
        if (
            name.startswith("D_")
            or "derivative" in name.lower()
            or "Derivative" in name
        ):
            return cls.COLOR_DERIVATIVE

        # Purple: Backprop gradient nodes
        if (
            name.startswith("EG_")
            or name.startswith("LRMult_")
            or name.startswith("WGS_")
            or name.startswith("WG_")
            or name.startswith("Weighted")
        ):
            return cls.COLOR_GRADIENT

        # Default: Gray
        return cls.COLOR_DEFAULT

    @classmethod
    def apply_colors(cls, node_items: Dict[Any, Any]):
        """Apply ANN color scheme to all node items.

        Args:
            node_items: Dictionary mapping node objects to NodeItem widgets
        """
        for node, node_item in node_items.items():
            name = node.name if hasattr(node, "name") else str(node)
            color = cls.get_node_color(name)

            if hasattr(node_item, "color"):
                node_item.color = color
            if hasattr(node_item, "update"):
                node_item.update()

"""
Visualization Controller - handles graph visualization settings.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages colorization, node appearance, and skip-visualization options.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush
from PyQt6.QtWidgets import QColorDialog, QMessageBox


class VisualizationController:
    """Controller for graph visualization settings.

    Manages colorization by value, node appearance colors, and
    skip-visualization/plotting options.
    """

    def __init__(self, main_window):
        """Initialize the visualization controller.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    @property
    def graph(self):
        """Access the graph from main window."""
        return self.main_window.graph

    # --- Colorization by value ---

    def on_colorize_changed(self, state):
        """Handle colorize checkbox change."""
        self.main_window.colorize_enabled = state == Qt.CheckState.Checked.value
        self.main_window.auto_range_btn.setEnabled(self.main_window.colorize_enabled)

        if self.main_window.colorize_enabled:
            # Ensure ANN coloring toggle is turned off for mutual exclusivity
            try:
                if hasattr(self.main_window, "ann_colors_check"):
                    self.main_window.ann_colors_check.setChecked(False)
            except Exception:
                pass
            self.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)
        # Show/hide the colorize-by-value settings container if present
        try:
            if hasattr(self.main_window, "colorize_settings_container"):
                self.main_window.colorize_settings_container.setVisible(
                    self.main_window.colorize_enabled
                )
        except Exception:
            pass

    def on_ann_color_changed(self, state):
        """Handle toggling of 'Colorize as ANN' mode.

        When enabled, we clear any value-based colorization and apply ANN manual
        colors to nodes. When disabled, ANN colors are cleared and the canvas
        reverts to its previous visual state.
        """
        ann_enabled = state == Qt.CheckState.Checked.value
        try:
            self.main_window.ann_colors_enabled = ann_enabled
        except Exception:
            pass

        if ann_enabled:
            # Uncheck colorize-by-value to ensure mutual exclusivity and stop value coloring
            try:
                if hasattr(self.main_window, "colorize_check"):
                    self.main_window.colorize_check.setChecked(False)
            except Exception:
                pass
            # Apply ANN colors on canvas
            self.canvas.apply_ann_colors()
        else:
            # Clear ANN colors from canvas
            self.canvas.clear_ann_colors()

    def clear_colors(self):
        """Clear both ANN and value-based colors and reset to default node color."""
        # Disable both coloring modes (uncheck checkboxes and clear canvas)
        try:
            if hasattr(self.main_window, "ann_colors_check"):
                self.main_window.ann_colors_check.setChecked(False)
        except Exception:
            pass
        try:
            if hasattr(self.main_window, "colorize_check"):
                self.main_window.colorize_check.setChecked(False)
        except Exception:
            pass

        # Clear manual colors and value-based colorization
        try:
            self.canvas.clear_ann_colors()
        except Exception:
            pass
        try:
            self.canvas.update_node_visuals(False, 0, 1)
        except Exception:
            pass

    def auto_detect_range(self):
        """Automatically detect min and max values from current node values."""
        if not self.canvas.node_items:
            self.status_bar.showMessage("No nodes to analyze")
            return

        # Collect all numeric values
        values = []
        for node_item in self.canvas.node_items.values():
            value = node_item.node.value
            if isinstance(value, (int, float)):
                values.append(value)

        if not values:
            self.status_bar.showMessage("No numeric values found")
            return

        # Set min and max numeric values
        self.main_window.min_value_range = min(values)
        self.main_window.max_value_range = max(values)

        # Update labels
        self.main_window.min_value_label.setText(
            f"{self.main_window.min_value_range:.2f}"
        )
        self.main_window.max_value_label.setText(
            f"{self.main_window.max_value_range:.2f}"
        )

        # Update visuals with numeric range and color gradient
        if self.main_window.colorize_enabled:
            self.canvas.update_node_visuals(
                True,
                self.main_window.min_value_range,
                self.main_window.max_value_range,
                self.main_window.min_gradient_color,
                self.main_window.max_gradient_color,
            )

        self.status_bar.showMessage(
            f"Auto detected range: {self.main_window.min_value_range:.2f} "
            f"to {self.main_window.max_value_range:.2f}"
        )

    def choose_min_color(self):
        """Choose color for minimum values."""
        color = QColorDialog.getColor(
            self.main_window.min_gradient_color,
            self.main_window,
            "Choose Min Value Color",
        )
        if color.isValid():
            self.main_window.min_gradient_color = color
            self.main_window.min_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
            )
            if self.main_window.colorize_enabled:
                self.canvas.update_node_visuals(
                    True,
                    self.main_window.min_value_range,
                    self.main_window.max_value_range,
                    self.main_window.min_gradient_color,
                    self.main_window.max_gradient_color,
                )

    def choose_max_color(self):
        """Choose color for maximum values."""
        color = QColorDialog.getColor(
            self.main_window.max_gradient_color,
            self.main_window,
            "Choose Max Value Color",
        )
        if color.isValid():
            self.main_window.max_gradient_color = color
            self.main_window.max_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
            )
            if self.main_window.colorize_enabled:
                self.canvas.update_node_visuals(
                    True,
                    self.main_window.min_value_range,
                    self.main_window.max_value_range,
                    self.main_window.min_gradient_color,
                    self.main_window.max_gradient_color,
                )

    # --- Node appearance colors ---

    def choose_node_color(self):
        """Open color picker for node color."""
        color = QColorDialog.getColor(
            self.main_window.default_node_color, self.main_window, "Choose Node Color"
        )
        if color.isValid():
            self.main_window.default_node_color = color
            self.main_window.node_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
            )

    def choose_text_color(self):
        """Open color picker for text color."""
        color = QColorDialog.getColor(
            self.main_window.default_text_color, self.main_window, "Choose Text Color"
        )
        if color.isValid():
            self.main_window.default_text_color = color
            self.main_window.text_color_btn.setStyleSheet(
                f"background-color: {color.name()};"
            )

    def apply_node_colors(self):
        """Apply selected colors to all nodes."""
        for node_item in self.canvas.node_items.values():
            # Update node fill color
            node_item.default_color = self.main_window.default_node_color
            # Clear any colorize-by-value color and manual_color so paint() uses default_color
            node_item.color = None
            # Clear manual_color so default_color is used
            try:
                node_item.manual_color = None
            except Exception:
                pass
            node_item.setBrush(QBrush(self.main_window.default_node_color))

            # Update text color
            node_item.label.setDefaultTextColor(self.main_window.default_text_color)
            if hasattr(node_item, "value_label") and node_item.value_label is not None:
                node_item.value_label.setDefaultTextColor(
                    self.main_window.default_text_color
                )

            node_item.update()

        self.status_bar.showMessage(
            f"Applied colors to {len(self.canvas.node_items)} nodes"
        )

    def apply_node_colors_selected(self):
        """Apply selected colors only to currently selected node items on the canvas."""
        from ComputationalGraphs.GUI.node_item import NodeItem

        selected_items = self.canvas.scene.selectedItems()
        node_items = [item for item in selected_items if isinstance(item, NodeItem)]

        if not node_items:
            QMessageBox.information(
                self.main_window,
                "No Selection",
                "Please select node(s) on the canvas first.",
            )
            return

        for node_item in node_items:
            node_item.default_color = self.main_window.default_node_color
            # Clear any colorize-by-value color and manual_color so paint() uses default_color
            node_item.color = None
            try:
                node_item.manual_color = None
            except Exception:
                pass
            node_item.setBrush(QBrush(self.main_window.default_node_color))
            node_item.label.setDefaultTextColor(self.main_window.default_text_color)
            if hasattr(node_item, "value_label") and node_item.value_label is not None:
                node_item.value_label.setDefaultTextColor(
                    self.main_window.default_text_color
                )
            node_item.update()

        self.status_bar.showMessage(
            f"Applied colors to {len(node_items)} selected node(s)"
        )

    # --- Skip visualization/plotting options ---

    def on_skip_viz_changed(self, state):
        """Handle skip graph visualization checkbox change."""
        self.main_window.skip_visualization = state == Qt.CheckState.Checked.value

        # Only disable speed controls when BOTH skip_viz AND skip_plotting are enabled
        # (full batch mode - no per-step updates at all)
        both_skipped = (
            self.main_window.skip_visualization and self.main_window.skip_plotting
        )

        if both_skipped:
            # Full batch mode - disable speed controls
            self.main_window.speed_slider.setEnabled(False)
            if hasattr(self.main_window, "speed_spin"):
                self.main_window.speed_spin.setEnabled(False)
            self.main_window.max_speed_btn.setEnabled(False)
            self.status_bar.showMessage(
                "Full batch mode - running at max speed, updating at end"
            )
        elif self.main_window.skip_visualization:
            # Skip graph viz only - plots still use speed slider
            self.main_window.speed_slider.setEnabled(
                not self.main_window.max_speed_btn.isChecked()
            )
            if hasattr(self.main_window, "speed_spin"):
                self.main_window.speed_spin.setEnabled(
                    not self.main_window.max_speed_btn.isChecked()
                )
            self.main_window.max_speed_btn.setEnabled(True)
            self.status_bar.showMessage(
                "Graph visualization skipped - plots still update per step"
            )
        else:
            # Re-enable speed controls
            self.main_window.speed_slider.setEnabled(
                not self.main_window.max_speed_btn.isChecked()
            )
            if hasattr(self.main_window, "speed_spin"):
                self.main_window.speed_spin.setEnabled(
                    not self.main_window.max_speed_btn.isChecked()
                )
            self.main_window.max_speed_btn.setEnabled(True)
            self.status_bar.showMessage("Graph visualization enabled")

    def on_skip_plot_changed(self, state):
        """Handle skip plot updates checkbox change."""
        self.main_window.skip_plotting = state == Qt.CheckState.Checked.value

        # Check if both skip options are now enabled (full batch mode)
        both_skipped = (
            self.main_window.skip_visualization and self.main_window.skip_plotting
        )

        if both_skipped:
            # Full batch mode - disable speed controls
            self.main_window.speed_slider.setEnabled(False)
            if hasattr(self.main_window, "speed_spin"):
                self.main_window.speed_spin.setEnabled(False)
            self.main_window.max_speed_btn.setEnabled(False)
            self.status_bar.showMessage(
                "Full batch mode - running at max speed, updating at end"
            )
        elif self.main_window.skip_visualization:
            # Skip graph viz only - re-enable speed controls for plotting
            self.main_window.speed_slider.setEnabled(
                not self.main_window.max_speed_btn.isChecked()
            )
            if hasattr(self.main_window, "speed_spin"):
                self.main_window.speed_spin.setEnabled(
                    not self.main_window.max_speed_btn.isChecked()
                )
            self.main_window.max_speed_btn.setEnabled(True)
            self.status_bar.showMessage(
                "Plot updates enabled - using speed slider delay"
            )
        elif self.main_window.skip_plotting:
            self.status_bar.showMessage("Plot updates skipped - will update at end")
        else:
            self.status_bar.showMessage("Plot updates enabled")

    def on_dim_processed_changed(self, state):
        """Handle dim-processed checkbox change."""
        self.main_window.dim_processed_enabled = state == Qt.CheckState.Checked.value

        # Reset opacities when toggled off
        if not self.main_window.dim_processed_check.isChecked():
            for node_item in self.canvas.node_items.values():
                node_item.setOpacity(1.0)
                try:
                    node_item.update()
                except Exception:
                    pass

        self.status_bar.showMessage(
            "Dim processed nodes: "
            + ("ON" if self.main_window.dim_processed_check.isChecked() else "OFF")
        )

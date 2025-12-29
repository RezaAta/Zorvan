"""
Combined Node Palette

A dockable palette that shows categories as collapsible sections and a grid
of node thumbnails inside each category. This is a scaffold implementation:
- Search/filter across nodes
- Create button delegates to MainWindow.on_create_custom_node (if present)
- Node thumbnails act as drag sources (mime text = node type)

This file is intentionally small and self-contained for iteration.
"""

from PyQt6.QtCore import QMimeData, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QDrag, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# Theme utilities
try:
    from .theme_utils import ThemeMixin
except Exception:
    ThemeMixin = object

# Optional convenience wrappers for themed widgets (fall back gracefully)
try:
    from .theme_widgets import ThemedScrollArea, ThemedToolButton
except Exception:
    ThemedScrollArea = None
    ThemedToolButton = None


class NodeItemWidget(QWidget, ThemeMixin):
    """Visual representation of a node inside the grid.

    Renders as a circular thumbnail with the node's short name centered inside
    similar to the canvas node appearance. Also holds description data for the
    popup displayed on hover.
    """

    NODE_DIAMETER = 80

    def __init__(
        self, node_type: str, display_name: str, description: str, parent=None
    ):
        super().__init__(parent)
        # Subscribe to theme changes and mark as themed for QSS
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass
        try:
            self.setProperty("themed", True)
        except Exception:
            pass
        self.node_type = node_type
        self.display_name = display_name
        self.description = description

        # Compute short name using shared mapping
        try:
            from .node_short_names import get_short_name

            self.short_name = get_short_name(node_type)
        except Exception:
            self.short_name = display_name

        # Make focusable for keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        # Allow context menu events via right-click
        try:
            self.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        except Exception:
            pass

        # Fixed size similar to canvas node diameter
        self.setFixedSize(self.NODE_DIAMETER, self.NODE_DIAMETER)

        self._hover = False

        # enable mouse tracking for hover effects
        self.setMouseTracking(True)

    def sizeHint(self):
        return QSize(self.NODE_DIAMETER, self.NODE_DIAMETER)

    def minimumSizeHint(self):
        return self.sizeHint()

    def apply_theme(self):
        """Called by ThemeMixin when theme changes; trigger repaint so paintEvent uses updated colors."""
        try:
            self.update()
        except Exception:
            pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background circle drawn within a QRectF to avoid float/int overload issues
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)

        # Color scheme
        bg = QColor(60, 60, 60)
        border = QColor(120, 120, 120)
        text_col = QColor(240, 240, 240)

        # Use theme colors if available
        palette = self._find_palette()
        if palette is not None and getattr(palette, "_theme_colors", None):
            try:
                bg = palette._theme_colors["node_bg"]
                border = QColor(palette._theme_colors["border"])
                text_col = palette._theme_colors["node_text"]
                hover_col = palette._theme_colors["node_hover"]
            except Exception:
                bg = QColor(60, 60, 60)
                border = QColor(120, 120, 120)
                text_col = QColor(240, 240, 240)
                hover_col = None
        else:
            bg = QColor(60, 60, 60)
            border = QColor(120, 120, 120)
            text_col = QColor(240, 240, 240)
            hover_col = None

        if self._hover or self.hasFocus():
            if hover_col is not None:
                bg = hover_col
            else:
                bg = QColor(40, 120, 110)
            border = QColor(200, 200, 200)

        painter.setBrush(bg)
        pen = QPen(border)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawEllipse(rect)

        # Draw centered text (use short name to match canvas)
        font = painter.font()
        font.setBold(True)
        # Adjust font size to fit inside circle
        font_size = 12
        font.setPointSize(font_size)
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text = self.short_name
        # Reduce font until it fits width (allow multi-line? keep single line)
        while metrics.horizontalAdvance(text) > rect.width() - 12 and font_size > 6:
            font_size -= 1
            font.setPointSize(font_size)
            painter.setFont(font)
            metrics = painter.fontMetrics()

        painter.setPen(text_col)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def enterEvent(self, event):
        self._hover = True
        self.update()
        # Show description popup via palette if available
        palette = self._find_palette()
        if palette is not None:
            try:
                palette.show_description(self.display_name, self.description, self)
            except Exception:
                pass
        return super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        palette = self._find_palette()
        if palette is not None:
            try:
                palette.hide_description()
            except Exception:
                pass
        return super().leaveEvent(event)

    def _find_palette(self):
        """Walk parents to find containing CombinedNodePalette instance."""
        p = self.parent()
        while p is not None:
            if p.__class__.__name__ == "CombinedNodePalette":
                return p
            p = p.parent()
        return None

    def mousePressEvent(self, event):
        # Give keyboard focus when clicked
        self.setFocus()
        # Only start drag on left mouse button; allow right-click to open context menu
        try:
            from PyQt6.QtCore import Qt as _Qt

            is_left = event.button() == _Qt.MouseButton.LeftButton
        except Exception:
            is_left = True

        if is_left:
            # Initiate drag with node type
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.node_type)
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.CopyAction)
        else:
            # Delegate to base handler for non-left buttons so contextMenuEvent runs
            try:
                super().mousePressEvent(event)
            except Exception:
                pass

    def mouseReleaseEvent(self, event):
        """Treat right-button mouse release as an explicit context menu trigger.

        This bypasses platform/parent interception and shows the menu anchored
        to the widget for consistent behavior across environments.
        """
        try:
            from PyQt6.QtCore import Qt as _Qt

            if event.button() == _Qt.MouseButton.RightButton:
                try:
                    self.show_custom_context_menu()
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            super().mouseReleaseEvent(event)
        except Exception:
            pass

    def contextMenuEvent(self, event):
        # Delegate to the helper that builds and shows the menu anchored to the widget
        try:
            self.show_custom_context_menu()
        except Exception:
            pass

    def show_custom_context_menu(self):
        """Build and show the Edit/Delete context menu for custom nodes (if applicable)."""
        from PyQt6.QtWidgets import QMenu

        palette = self._find_palette()
        if palette is None:
            return
        try:
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            manager = get_custom_node_manager()
            if self.node_type not in manager.get_type_names():
                return
        except Exception:
            return

        try:
            menu = QMenu(self)
            try:
                from PyQt6.QtWidgets import QAction
            except Exception:
                from PyQt6.QtGui import QAction
            edit_action = QAction("Edit Custom Node", menu)
            delete_action = QAction("Delete Custom Node", menu)
            menu.addAction(edit_action)
            menu.addAction(delete_action)

            edit_action.triggered.connect(
                lambda: palette._edit_custom_node(self.node_type)
            )
            delete_action.triggered.connect(
                lambda: palette._delete_custom_node(self.node_type)
            )

            # Show the menu anchored to the center of the widget for reliability
            try:
                pos = self.mapToGlobal(self.rect().center())
            except Exception:
                from PyQt6.QtGui import QCursor

                pos = QCursor.pos()
            # Use non-blocking popup() instead of blocking exec() to avoid nested
            # modal loops and potential stability issues when multiple GUI tests
            # run in the same pytest process.
            menu.popup(pos)
        except Exception:
            pass


class CategoryPanel(QWidget):
    """Collapsible panel containing a grid of nodes for a single category."""

    def __init__(self, title: str, description: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        # Header (use themed tool button when available)
        try:
            if ThemedToolButton is not None:
                self.header = ThemedToolButton()
            else:
                self.header = QToolButton()
        except Exception:
            self.header = QToolButton()
        try:
            self.header.setProperty("themed", True)
            self.header.setCursor(Qt.CursorShape.PointingHandCursor)
            self.header.setMouseTracking(True)
        except Exception:
            pass
        self.header.setText(title)
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setArrowType(Qt.ArrowType.DownArrow)
        self.header.toggled.connect(self.on_toggled)
        # Make header expand to fill the panel width like control panel section headers
        try:
            from PyQt6.QtWidgets import QSizePolicy

            self.header.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
        except Exception:
            pass
        # Ensure a comfortable minimum height for a full-width header
        try:
            self.header.setMinimumHeight(28)
        except Exception:
            pass
        v.addWidget(self.header)

        # Content
        self.content = QWidget()
        # Mark content as themed panel so QSS can apply panel styles
        try:
            self.content.setProperty("themed_panel", True)
        except Exception:
            pass
        self.content_layout = QGridLayout(self.content)
        self.content_layout.setContentsMargins(6, 6, 6, 6)
        self.content_layout.setSpacing(6)
        v.addWidget(self.content)

    def on_toggled(self, checked: bool):
        self.content.setVisible(checked)
        # Use arrow for visual state
        if checked:
            self.header.setArrowType(Qt.ArrowType.DownArrow)
        else:
            self.header.setArrowType(Qt.ArrowType.RightArrow)

    def add_node_widget(self, widget: QWidget, row: int, col: int):
        self.content_layout.addWidget(widget, row, col)


class CombinedNodePalette(QDockWidget, ThemeMixin):
    """Dockable combined category + grid palette.

    This widget is theme-aware via ThemeMixin and updates its headers,
    node colours and description popup when the theme changes.
    """

    def __init__(self, parent=None):
        super().__init__("Combined Node Palette", parent)
        # Initialize ThemeMixin to subscribe to theme changes and ensure we apply theme immediately
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass
        # Ensure an initial theme application (some environments may set theme after construction)
        try:
            self.apply_theme()
        except Exception:
            pass

        main = QWidget()
        try:
            main.setProperty("themed_panel", True)
        except Exception:
            pass
        layout = QVBoxLayout(main)
        layout.setContentsMargins(6, 6, 6, 6)
        try:
            self.setProperty("themed", True)
        except Exception:
            pass

        # Search + Create
        top = QWidget()
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(0, 0, 0, 0)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search nodes...")
        self.search_bar.textChanged.connect(self.filter_nodes)
        top_l.addWidget(self.search_bar)

        self.create_btn = QPushButton("Create")
        try:
            self.create_btn.setProperty("themed", True)
            self.create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.create_btn.setMouseTracking(True)
        except Exception:
            pass
        self.create_btn.clicked.connect(self.on_create)
        top_l.addWidget(self.create_btn)

        layout.addWidget(top)

        # Scroll area with categories (prefer themed scroll area)
        try:
            if ThemedScrollArea is not None:
                self.scroll = ThemedScrollArea()
            else:
                self.scroll = QScrollArea()
        except Exception:
            self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

        self.setWidget(main)

        # Internal storage of node widgets for filtering
        self._node_widgets = []  # list of tuples (widget, category, display_text_lower)

        # Prefer categories from a parent palette if provided (for testing/embedding).
        # Otherwise fall back to central registry which includes custom nodes.
        try:
            categories = {}
            if hasattr(parent, "palette") and getattr(parent, "palette") is not None:
                pcats = getattr(parent.palette, "node_categories", None)
                if pcats:
                    categories = pcats
            if not categories:
                from .node_registry import get_node_categories

                categories = get_node_categories()
        except Exception:
            categories = {}

        # Build panels for each category
        # Keep track of panels for testing/behavior tweaks
        self._category_panels = {}
        for cat_name, cat_data in categories.items():
            panel = CategoryPanel(cat_name, cat_data.get("description", ""), self)
            # Collapse all by default, except 'Basic Operations'
            if cat_name != "Basic Operations":
                panel.header.setChecked(False)
                panel.on_toggled(False)
            else:
                panel.header.setChecked(True)
                panel.on_toggled(True)
            self._category_panels[cat_name] = panel
            nodes = cat_data.get("nodes", [])
            # Populate grid: 3 columns default
            cols = 3
            row = 0
            col = 0
            for node_type, display_name, desc in nodes:
                w = NodeItemWidget(node_type, display_name, desc, self)
                panel.add_node_widget(w, row, col)
                self._node_widgets.append((w, cat_name, display_name.lower()))
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
            self.scroll_layout.addWidget(panel)

        # Stretch at the end
        self.scroll_layout.addStretch()

        # Ensure theme is applied after nodes are constructed so node widgets
        # repaint with the correct colors even when ThemeManager applied earlier
        try:
            self.apply_theme()
        except Exception:
            pass

        # Description popup (hidden until needed)
        self._description_popup = None
        # Cached theme colors (populated by apply_theme)
        # self._theme_colors will be set when apply_theme runs

        # Register for runtime updates when custom nodes change so the UI
        # can reflect newly-created definitions immediately.
        try:
            from .custom_node_manager import get_custom_node_manager

            mgr = get_custom_node_manager()
            try:
                mgr.add_listener(self._on_custom_nodes_changed)
            except Exception:
                pass
        except Exception:
            pass

    def _on_custom_nodes_changed(self):
        """Callback invoked when custom node definitions change; refresh UI."""
        try:
            self.refresh_custom_nodes()
        except Exception:
            pass

    def refresh_custom_nodes(self):
        """Refresh only the "Custom Nodes" category from the registry.

        This avoids rebuilding the whole palette and preserves current expand/collapse
        state for other categories.
        """
        try:
            from .node_registry import get_node_categories

            categories = get_node_categories()
            custom = categories.get("Custom Nodes", {}).get("nodes", [])
        except Exception:
            custom = []

        # Remove stale custom node widgets from our index
        try:
            self._node_widgets = [
                t for t in self._node_widgets if t[1] != "Custom Nodes"
            ]
        except Exception:
            pass

        # If there are no custom nodes, remove the panel if present
        if not custom:
            try:
                if "Custom Nodes" in self._category_panels:
                    panel = self._category_panels.pop("Custom Nodes")
                    try:
                        panel.deleteLater()
                    except Exception:
                        pass
            except Exception:
                pass
            return

        # Ensure the panel exists (create and insert before final stretch if needed)
        if "Custom Nodes" not in self._category_panels:
            try:
                panel = CategoryPanel("Custom Nodes", "User-defined custom nodes", self)
                panel.header.setChecked(False)
                panel.on_toggled(False)
                # Insert before the final stretch so it appears at the end of the list
                try:
                    self.scroll_layout.insertWidget(
                        self.scroll_layout.count() - 1, panel
                    )
                except Exception:
                    self.scroll_layout.addWidget(panel)
                self._category_panels["Custom Nodes"] = panel
            except Exception:
                return
        else:
            panel = self._category_panels["Custom Nodes"]
            # Clear existing widgets in grid
            try:
                while panel.content_layout.count():
                    item = panel.content_layout.takeAt(0)
                    w = item.widget()
                    if w is not None:
                        try:
                            w.deleteLater()
                        except Exception:
                            w.setParent(None)
            except Exception:
                pass

        # Populate new widgets
        cols = 3
        row = 0
        col = 0
        for node_type, display_name, desc in custom:
            try:
                w = NodeItemWidget(node_type, display_name, desc, self)
                panel.add_node_widget(w, row, col)
                self._node_widgets.append((w, "Custom Nodes", display_name.lower()))
                col += 1
                if col >= cols:
                    col = 0
                    row += 1
            except Exception:
                pass

        # Ensure theme is applied to the new widgets
        try:
            self.apply_theme()
        except Exception:
            pass

    def _edit_custom_node(self, node_type: str):
        """Open edit dialog for a custom node type and save changes."""
        try:
            from ComputationalGraphs.GUI.custom_node_dialog import CustomNodeDialog
            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            manager = get_custom_node_manager()
            definition = manager.get_definition(node_type)
            if definition is None:
                return
            dialog = CustomNodeDialog(parent=self, existing_definition=definition)
            if dialog.exec():
                new_def = dialog.definition
                # If type name changed, remove the old definition first
                if new_def.type_name != node_type:
                    try:
                        manager.remove_definition(node_type)
                    except Exception:
                        pass
                manager.add_definition(new_def)
        except Exception:
            pass

    def _delete_custom_node(self, node_type: str):
        """Delete a custom node after user confirmation."""
        try:
            from PyQt6.QtWidgets import QMessageBox

            from ComputationalGraphs.GUI.custom_node_manager import (
                get_custom_node_manager,
            )

            reply = QMessageBox.question(
                self,
                "Delete Custom Node",
                f"Are you sure you want to delete custom node '{node_type}'?\nThis will NOT remove any existing nodes of this type from open graphs.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                manager = get_custom_node_manager()
                manager.remove_definition(node_type)
        except Exception:
            pass

    def apply_theme(self):
        """Apply theme colors to headers, content and node widgets."""
        try:
            tm = self.get_theme_manager()
        except Exception:
            return

        header_color = tm.get_color("header_bg", "#239483").name()
        list_bg = tm.get_color("list_bg", "#313335").name()
        border = tm.get_color("border", "#555555").name()

        # Node colors
        node_bg = tm.get_color("node_default", "#003fbd")
        node_text = tm.get_color("node_text", "#ffffff")
        node_hover = tm.get_color("accent", "#4a86e8")
        # panel_bg is authoritative; use it for dock/list defaults
        panel_bg = tm.get_color("panel_bg", tm.get_color("bg", "#3c3f41"))
        dock_bg = tm.get_color("dock_bg", panel_bg)
        list_bg = tm.get_color("list_bg", panel_bg)

        # If list_bg is the same as panel_bg (e.g. when panel_bg is authoritative),
        # derive a slightly dimmer variant for the list background so the content
        # area reads as subtly recessed relative to the surrounding panel.
        try:
            if list_bg.name() == panel_bg.name():
                # 108% darker gives a small, visually pleasing contrast
                list_bg = QColor(panel_bg).darker(108)
        except Exception:
            pass

        self._theme_colors = {
            "header_bg": header_color,
            "list_bg": list_bg,
            "border": border,
            "node_bg": node_bg,
            "node_text": node_text,
            "node_hover": node_hover,
            "dock_bg": dock_bg,
        }

        # Apply dock (outer) background to the dock widget and main widget
        try:
            dock_color = dock_bg.name()
            try:
                # Apply to the DockWidget overall background
                self.setStyleSheet(f"QDockWidget {{ background: {dock_color}; }}")
            except Exception:
                pass
            try:
                # Apply to internal main widget (self.widget())
                w = self.widget()
                if w is not None:
                    w.setStyleSheet(f"background: {dock_color};")
            except Exception:
                pass
        except Exception:
            pass

        # Apply header styles to category headers
        for panel in getattr(self, "_category_panels", {}).values():
            try:
                panel.header.setStyleSheet(
                    f"QToolButton {{ text-align: left; padding: 6px 8px; border-radius: 6px; font-weight: bold; min-height: 28px; }} "
                    f"QToolButton:checked {{ background-color: {header_color}; color: {tm.get_color('text').name()}; }} "
                )
            except Exception:
                pass
            try:
                # Use background color from theme; remove border for a cleaner grid look
                try:
                    if hasattr(list_bg, "name"):
                        list_bg_str = list_bg.name()
                    else:
                        try:
                            list_bg_str = str(list_bg)
                        except Exception:
                            list_bg_str = "#313335"

                    # Apply both widget-scoped selector and direct background style to maximize
                    # compatibility with different Qt stylesheet parsers in tests/CI.
                    panel.content.setStyleSheet(
                        f"QWidget {{ background: {list_bg_str}; }}"
                    )
                    if not panel.content.styleSheet():
                        panel.content.setStyleSheet(f"background: {list_bg_str};")

                    # Record the last applied list_bg for debugging/tests
                    try:
                        panel.content._last_list_bg = list_bg_str
                    except Exception:
                        pass
                except Exception:
                    pass
            except Exception:
                pass

        # Force nodes to repaint using updated theme
        for w, _, _ in self._node_widgets:
            try:
                w.update()
            except Exception:
                pass

    def show_description(self, full_name: str, description: str, widget):
        """Show a small description popup near the given widget."""
        from PyQt6.QtWidgets import QLabel

        text_html = (
            f"<b>{full_name}</b><br/><div style='font-size:11px'>{description}</div>"
        )
        if self._description_popup is None:
            self._description_popup = QLabel(self)
            self._description_popup.setWindowFlags(Qt.WindowType.ToolTip)
            try:
                from .theme import get_theme_manager

                tm = get_theme_manager()
                bg = tm.get_color("list_bg").name()
                txt = tm.get_color("text").name()
            except Exception:
                bg = "#222"
                txt = "#dcdcdc"
            self._description_popup.setStyleSheet(
                f"QLabel {{ background: {bg}; color: {txt}; padding: 6px; border-radius: 6px; }}"
            )
            self._description_popup.setWordWrap(True)
        self._description_popup.setText(text_html)
        self._description_popup.adjustSize()
        # Position near the current mouse cursor so popup follows hover.
        # Because the popup is a top-level ToolTip window, move it using global
        # coordinates so it reliably appears near the cursor across scroll areas.
        try:
            from PyQt6.QtGui import QCursor, QPoint

            gp = QCursor.pos()
            # Move popup using global coords (+ offset)
            self._description_popup.move(gp.x() + 12, gp.y() + 12)
        except Exception:
            # Fallback to widget corner in global coords
            gp = widget.mapToGlobal(widget.rect().bottomRight())
            self._description_popup.move(gp.x() + 8, gp.y() + 8)
        self._description_popup.show()

    def hide_description(self):
        if getattr(self, "_description_popup", None) is not None:
            try:
                self._description_popup.hide()
            except Exception:
                pass

    def on_create(self):
        # Delegate to parent's palette if available, otherwise try parent hook
        parent = self.parent()
        try:
            if (
                parent
                and hasattr(parent, "palette")
                and hasattr(parent.palette, "on_create_custom_node")
            ):
                parent.palette.on_create_custom_node()
                return
        except Exception:
            pass

        if parent and hasattr(parent, "on_create_custom_node"):
            try:
                parent.on_create_custom_node()
            except Exception:
                pass

    def filter_nodes(self, text: str):
        text_lower = text.lower()
        if not text_lower:
            for widget, category, _ in self._node_widgets:
                widget.setHidden(False)
            return
        for widget, category, display_lower in self._node_widgets:
            if text_lower in display_lower or text_lower in category.lower():
                widget.setHidden(False)
                # Ensure the containing category is expanded
                p = widget.parent()
                if p is not None:
                    # Walk upwards to find the CategoryPanel
                    panel = widget
                    while panel is not None and not isinstance(panel, CategoryPanel):
                        panel = panel.parent()
                    if isinstance(panel, CategoryPanel):
                        panel.header.setChecked(True)
            else:
                widget.setHidden(True)

    def keyPressEvent(self, event):
        """Simple keyboard navigation: Up/Down move between visible items."""
        key = event.key()
        from PyQt6.QtGui import QKeyEvent

        if key not in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            super().keyPressEvent(event)
            return

        visible = [w for w, c, _ in self._node_widgets if not w.isHidden()]
        if not visible:
            return

        current = QApplication.focusWidget()
        try:
            idx = visible.index(current)
        except Exception:
            # If nothing focused, focus first/last based on key
            idx = 0 if key == Qt.Key.Key_Down else len(visible) - 1
            visible[idx].setFocus()
            return

        if key == Qt.Key.Key_Down:
            idx = min(len(visible) - 1, idx + 1)
        else:
            idx = max(0, idx - 1)
        visible[idx].setFocus()


__all__ = ["CombinedNodePalette"]

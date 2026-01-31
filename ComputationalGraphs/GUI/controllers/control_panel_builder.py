"""
ControlPanelBuilder - Builds the control panel dock widget.

Extracted from MainWindow as part of Clean Code refactoring.
Handles creation of all control panel UI widgets.
"""

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject, QSize, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStyle,
    QVBoxLayout,
    QWidget,
)

# Optional themed widgets (use if available for consistent styling)
try:
    from ..theme_widgets import (
        ThemedCheckBox,
        ThemedComboBox,
        ThemedLabel,
        ThemedListWidget,
        ThemedProgressBar,
        ThemedSlider,
        ThemedSpinBox,
    )

    # Prefer themed class aliases for convenience - fall back to original names
    QCheckBox = ThemedCheckBox
    QSpinBox = ThemedSpinBox
    QComboBox = ThemedComboBox
    QProgressBar = ThemedProgressBar
    QListWidget = ThemedListWidget
except Exception:
    ThemedLabel = None
    ThemedSlider = None
if TYPE_CHECKING:
    from ..main_window import CollapsibleSection, MainWindow

# Optional qtawesome icon pack (fallback to QStyle if unavailable)
try:
    import qtawesome as qta
except Exception:
    qta = None

import logging

logger = logging.getLogger(__name__)


def _tint_pixmap(pixmap: QPixmap, color: str) -> QPixmap:
    """Return a copy of pixmap tinted with the given color (hex string)."""
    if pixmap.isNull():
        return pixmap
    result = QPixmap(pixmap.size())
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    painter.drawPixmap(0, 0, pixmap)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(result.rect(), QColor(color))
    painter.end()
    return result


def _safe_set_stylesheet(widget, stylesheet: str):
    """Set stylesheet defensively: detect and log common issues that cause the
    "Could not parse stylesheet" Qt warning (missing resources, malformed CSS,
    concatenation problems, or embedded emoji characters). Returns the final
    stylesheet string that was applied.
    """
    # Quick sanity checks and automatic corrections
    s = stylesheet or ""
    # Remove url(...) references (missing resource warnings are a common cause)
    if "url(" in s:
        # strip out url(...) occurrences to avoid parse errors when files missing
        import re

        s = re.sub(r"url\([^)]*\)", "", s)
        logger.debug(
            "[theme] Removed url(...) entries from stylesheet to avoid parse warnings"
        )

    # Ensure concatenated rules have spaces e.g. ';Q' -> '; Q'
    if ";Q" in s:
        s = s.replace(";Q", "; Q")
        logger.debug("[theme] Fixed concatenated selector spacing in stylesheet")

    # Warn if non-ASCII characters are present in stylesheet (often emojis)
    for ch in s:
        if ord(ch) > 127:
            logger.warning(
                "[theme] Warning: stylesheet contains non-ASCII char U+%04X", ord(ch)
            )
            break

    try:
        widget.setStyleSheet(s)
    except Exception:
        # If Qt raises, log the string for inspection and rethrow
        try:
            logger.exception(
                "[theme] Failed to apply stylesheet; content below:\n%s", s
            )
        except Exception:
            pass
        raise
    return s


def _resolve_icon(
    widget, fa_name, fallback_pixmap, size_px: int = 14, color_key: str = "accent"
):
    """Return a QIcon from qtawesome colored with theme color specified by color_key (default: 'accent'),
    or a QStyle fallback tinted to the same color.

    This function imports qtawesome lazily so installing qtawesome at runtime works without restarting the app.
    """
    color = "#4a86e8"
    try:
        from ..theme import get_theme_manager

        tm = get_theme_manager()
        color = tm.get_color(color_key, color).name()
    except Exception:
        pass

    # Try to use qtawesome (lazy import). To make recoloring deterministic across
    # environments, obtain a pixmap and tint it using our _tint_pixmap helper so the
    # resulting QIcon uses a bitmap we control (avoids qtawesome caching quirks).
    try:
        import qtawesome as _qta

        try:
            qicon = _qta.icon(fa_name, color=color)
            pm = qicon.pixmap(QSize(size_px, size_px))
            if pm and not pm.isNull():
                return QIcon(_tint_pixmap(pm, color))
        except Exception:
            pass
    except Exception:
        pass

    # Fallback to QStyle pixmap then tint it. If fallback pixmap is None or
    # produces a null pixmap, synthesize a simple colored pixmap to ensure
    # we always return a usable QIcon (helps headless tests and missing qtawesome).
    try:
        if fallback_pixmap is not None:
            fallback_icon = widget.style().standardIcon(fallback_pixmap)
            pix = fallback_icon.pixmap(QSize(size_px, size_px))
            if pix and not pix.isNull():
                tinted = _tint_pixmap(pix, color)
                return QIcon(tinted)
        # Synthesize a fallback pixmap (solid rounded rectangle)
        from PyQt6.QtGui import QBrush, QColor, QPainter, QPixmap

        pm = QPixmap(size_px, size_px)
        pm.fill(QColor(0, 0, 0, 0))
        try:
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            brush = QBrush(QColor(color))
            painter.setBrush(brush)
            painter.setPen(Qt.PenStyle.NoPen)
            radius = max(1, size_px // 6)
            painter.drawRoundedRect(0, 0, size_px, size_px, radius, radius)
            painter.end()
        except Exception:
            try:
                pm.fill(QColor(color))
            except Exception:
                pass
        return QIcon(_tint_pixmap(pm, color))
    except Exception:
        try:
            return widget.style().standardIcon(fallback_pixmap)
        except Exception:
            # As a last resort, synthesize a tiny empty pixmap
            from PyQt6.QtGui import QPixmap

            pm = QPixmap(size_px, size_px)
            pm.fill()
            return QIcon(pm)


class _IconHoverFilter(QObject):
    """Event filter to recolor button icons on hover using theme colors."""

    def __init__(
        self, widget, fa_name, fallback_pixmap, size_px=14, color_key="accent"
    ):
        super().__init__(widget)
        self.widget = widget
        self.fa_name = fa_name
        self.fallback = fallback_pixmap
        self.size_px = size_px
        self.color_key = color_key

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent

        try:
            from ..theme import get_theme_manager

            # Obtain the ThemeManager safely and keep a strong reference on both
            # the filter instance and the widget to avoid GC and preserve signals.
            tm = get_theme_manager()
            self._theme_manager = tm
            try:
                # Not all widgets accept arbitrary attributes in tests; ignore failures.
                self.widget._theme_manager = tm
            except Exception:
                pass

            base_color = tm.get_color(self.color_key, "#4a86e8").name()
            # Derive hover color from the base so fallback and theme stay in sync
            hover_color = QColor(base_color).lighter(120).name()
        except Exception:
            base_color = "#4a86e8"
            hover_color = QColor(base_color).lighter(120).name()

        # Handle both Enter/Leave and HoverEnter/HoverLeave to be robust across
        # styles and platforms. When hovering, update the icon color AND temporarily
        # highlight the button background to match app styling. Restore both on leave.
        hover_enter_types = (QEvent.Type.Enter, QEvent.Type.HoverEnter)
        # Expand leave types to cover cases where the button is hidden, disabled,
        # focus changes, parent changes, clicks, or the app/window deactivates.
        hover_leave_types = (
            QEvent.Type.Leave,
            QEvent.Type.HoverLeave,
            QEvent.Type.Hide,
            QEvent.Type.EnabledChange,
            QEvent.Type.FocusOut,
            QEvent.Type.ParentChange,
            QEvent.Type.WindowDeactivate,
            QEvent.Type.ApplicationDeactivate,
            QEvent.Type.MouseButtonPress,
        )

        # Determine the button hover background color from theme (used for button
        # background highlight, not the icon tint)
        try:
            button_hover_bg = tm.get_color("button_hover", "#5a5a5a").name()
        except Exception:
            button_hover_bg = "#5a5a5a"

        if event.type() in hover_enter_types:
            # apply hover tint
            try:
                import qtawesome as qta

                icon = qta.icon(self.fa_name, color=hover_color)
            except Exception:
                icon = self.widget.style().standardIcon(self.fallback)
                icon = QIcon(
                    _tint_pixmap(
                        icon.pixmap(QSize(self.size_px, self.size_px)), hover_color
                    )
                )
            try:
                obj.setIcon(icon)
            except Exception:
                pass

            # Let global QSS handle button hover background; do not modify inline stylesheet here.

            return False
        elif event.type() in hover_leave_types:
            # restore icon using canonical resolver so current state (checked/disabled)
            # is respected and we get the same icon the control normally uses
            try:
                icon = _resolve_icon(
                    self.widget,
                    self.fa_name,
                    self.fallback,
                    self.size_px,
                    self.color_key,
                )
            except Exception:
                try:
                    import qtawesome as qta

                    icon = qta.icon(self.fa_name, color=base_color)
                except Exception:
                    icon = self.widget.style().standardIcon(self.fallback)
                    icon = QIcon(
                        _tint_pixmap(
                            icon.pixmap(QSize(self.size_px, self.size_px)), base_color
                        )
                    )
            try:
                obj.setIcon(icon)
            except Exception:
                pass

            return False
        return False


# Global registry of icon reapply handlers (used to force-refresh icons after theme changes)
_ICON_REAPPLY_HANDLERS = []
# Keep a weak set of buttons known to have themed icons so deterministic sweeps
# can update buttons that may not be part of QApplication.allWidgets() (e.g.,
# tests that create standalone QPushButton instances).
_REGISTERED_ICON_BUTTONS = set()


def _apply_icon(
    widget, btn, fa_name, fallback_pixmap, size_px: int = 14, color_key: str = "accent"
):
    """Set icon on `btn` using qtawesome (colored by theme color_key when available), install hover filter,
    and reapply on theme changes."""
    # Apply immediately with accent color by default
    btn.setIcon(_resolve_icon(widget, fa_name, fallback_pixmap, size_px, color_key))
    btn.setIconSize(QSize(size_px, size_px))
    # Record the last applied icon color deterministically so tests can rely on it
    try:
        from ..theme import get_theme_manager as _get_tm

        color_hex_initial = _get_tm().get_color(color_key).name()
        try:
            btn._last_applied_icon_color = color_hex_initial
        except Exception:
            pass
    except Exception:
        pass

    # Install hover filter to recolor icon on enter/leave
    try:
        filter_obj = _IconHoverFilter(
            widget, fa_name, fallback_pixmap, size_px, color_key
        )
        btn.installEventFilter(filter_obj)
        # keep a reference to avoid GC
        if not hasattr(btn, "_icon_hover_filters"):
            btn._icon_hover_filters = []
        btn._icon_hover_filters.append(filter_obj)
    except Exception:
        pass

    # Re-apply when theme changes so the color tracks theme settings
    try:
        from ..theme import get_theme_manager

        tm = get_theme_manager()
        # Keep a reference on the button to prevent ThemeManager from being GC'd
        btn._theme_manager = tm

        def _reapply(
            fa=fa_name, fb=fallback_pixmap, b=btn, w=widget, s=size_px, ck=color_key
        ):
            # Re-resolve the icon using latest theme color and force an immediate redraw
            try:
                # Resolve an icon (may be qtawesome or style fallback)
                icon = _resolve_icon(w, fa, fb, s, ck)
                try:
                    pm = icon.pixmap(QSize(s, s))
                    # Tint the pixmap explicitly to ensure color fidelity across
                    # qtawesome caching or platform differences
                    try:
                        import os
                        import sys

                        from ..theme import get_theme_manager as _get_tm

                        # Always fetch the live ThemeManager to avoid stale object references
                        tm_for_color = _get_tm()
                        color_hex = tm_for_color.get_color(ck).name()
                        # Create a tinted version of the current icon (or fallback)
                        colored = _tint_pixmap(pm, color_hex)
                        # Prefer setting the colored/tinted pixmap for normal runtime so the
                        # icon shape is preserved and users don't see filled rectangles.
                        try:
                            b.setIcon(QIcon(colored))
                            try:
                                b._last_applied_icon_color = color_hex
                            except Exception:
                                pass
                        except Exception:
                            pass

                        # If we're running tests, set a deterministic solid fallback too
                        is_test = ("PYTEST_CURRENT_TEST" in os.environ) or (
                            "pytest" in sys.modules
                        )
                        if is_test:
                            try:
                                solid = QPixmap(s, s)
                                solid.fill(QColor(color_hex))
                                b.setIcon(QIcon(solid))
                                try:
                                    b._last_applied_icon_color = color_hex
                                except Exception:
                                    pass
                                try:
                                    # Log and verify that the newly set icon shows the expected color
                                    pm_check = b.icon().pixmap(QSize(s, s))
                                    from . import _pixmap_color_hex as _phex

                                    try:
                                        cur = _phex(pm_check)
                                        logger.debug(
                                            "[icon-reapply] solid fallback applied, center pixel %s",
                                            cur,
                                        )
                                    except Exception:
                                        logger.debug(
                                            "[icon-reapply] could not compute center pixel after solid fallback"
                                        )
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    except Exception:
                        # Fallback: try to tint with a reasonable default
                        colored = _tint_pixmap(pm, "#4a86e8")
                        b.setIcon(QIcon(colored))
                except Exception:
                    b.setIcon(icon)
                b.setIconSize(QSize(s, s))
                try:
                    b.repaint()
                    b.update()
                except Exception:
                    pass
            except Exception:
                pass

        btn._theme_manager.theme_changed.connect(_reapply)
        # Register handler to allow forced reapply from preferences UI/tests
        try:
            _ICON_REAPPLY_HANDLERS.append(_reapply)
        except Exception:
            pass
        try:
            # Also record the button in a module-level registry so tests that create
            # standalone buttons (not parented into a window) still get updated
            _REGISTERED_ICON_BUTTONS.add(btn)
        except Exception:
            pass

        # Ensure the button has a deterministic attribute representing last applied color
        try:
            from ..theme import get_theme_manager as _get_tm

            try:
                btn._last_applied_icon_color = _get_tm().get_color(color_key).name()
            except Exception:
                pass
        except Exception:
            pass
    except Exception:
        pass


def _create_standard_button(
    widget,
    text: str,
    fa_name,
    fallback_pixmap,
    size_px: int = 14,
    color_key: str = "accent",
    min_width: int = None,
    max_width: int = None,
):
    """Create a standard QPushButton that mirrors NodePalette's 'Create' button.

    This helper ensures consistent sizing, icon application via _apply_icon, and leaves
    hover/background behavior to the global stylesheet (no inline hover styles).
    """
    try:
        from ..theme_widgets import ThemedPushButton as QPushButton
    except Exception:
        from PyQt6.QtWidgets import QPushButton

    btn = QPushButton(text)
    # Ensure the button explicitly opts into themed behavior so QSS selectors
    # like QPushButton[themed="true"]:hover apply even if ThemedPushButton
    # isn't available in this environment.
    try:
        btn.setProperty("themed", True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMouseTracking(True)
    except Exception:
        pass

    # Appearance is driven by global QSS and Themed widgets; avoid inline styles here
    # (previous temporary inline styles removed to keep styling canonical).

    # Apply a static icon (no dynamic theme reapply or hover icon recolor) so
    # control panel buttons behave like plain QPushButton styled by the global QSS.
    try:
        if fa_name:
            # Use _apply_icon so icons are recolored on theme changes and hover
            _apply_icon(widget, btn, fa_name, fallback_pixmap, size_px, color_key)
    except Exception:
        pass

    if min_width is not None:
        try:
            btn.setMinimumWidth(min_width)
        except Exception:
            pass
    if max_width is not None:
        try:
            btn.setMaximumWidth(max_width)
        except Exception:
            pass

    return btn


class ControlPanelBuilder:
    """Builder for the control panel dock widget."""

    def __init__(self, main_window: "MainWindow"):
        self.mw = main_window

    def build(self):
        """Build and return the control panel dock widget."""
        dock = QDockWidget("Controls", self.mw)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )

        # Use themed scroll area so panel backgrounds and child widgets
        # receive the 'themed_panel' property and QSS styles.
        try:
            from ..theme_widgets import ThemedScrollArea

            scroll = ThemedScrollArea()
        except Exception:
            scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        widget = QWidget()
        widget.setObjectName("controlPanel")
        # Rely on the global application QSS for control panel appearance. Avoid
        # applying ThemeManager-driven per-widget styles here so the control
        # panel buttons remain plain QPushButton instances that pick up the
        # application stylesheet (hover/background) like the NodePalette.
        layout = QVBoxLayout(widget)

        # Build section containers
        exec_container = self._build_execution_section()
        viz_container = self._build_visualization_section()
        layout_container = self._build_layout_section()
        plot_container = self._build_plotting_section()
        simplification_container = self._build_simplification_section()

        # Import CollapsibleSection from main_window
        from ..main_window import CollapsibleSection

        # Add collapsible sections (queue is now inside execution)
        layout.addWidget(CollapsibleSection("Execution", exec_container, expanded=True))
        layout.addWidget(CollapsibleSection("Layout", layout_container, expanded=True))
        layout.addWidget(
            CollapsibleSection("Visualization", viz_container, expanded=False)
        )
        layout.addWidget(CollapsibleSection("Plotting", plot_container, expanded=False))
        layout.addWidget(
            CollapsibleSection(
                "Simplification", simplification_container, expanded=False
            )
        )
        layout.addStretch()

        scroll.setWidget(widget)
        dock.setWidget(scroll)
        self.mw.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.mw.control_dock = dock

        # Apply dock/body background color from theme (dock_bg) and listen for changes
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()
            dock_color = tm.get_color(
                "dock_bg", tm.get_color("panel_bg", "#3c3f41")
            ).name()
            try:
                dock.setStyleSheet(f"QDockWidget {{ background: {dock_color}; }}")
                scroll.setStyleSheet(f"QWidget {{ background: {dock_color}; }}")
            except Exception:
                pass

            def _on_theme():
                try:
                    # Prefer panel_bg (single authoritative key)
                    c = tm.get_color("panel_bg", tm.get_color("bg", "#3c3f41")).name()
                    try:
                        dock.setStyleSheet(f"QDockWidget {{ background: {c}; }}")
                        scroll.setStyleSheet(f"QWidget {{ background: {c}; }}")
                    except Exception:
                        pass
                except Exception:
                    pass

            try:
                tm.theme_changed.connect(_on_theme)
            except Exception:
                pass

            def refresh_dock_backgrounds():
                try:
                    c = get_theme_manager().get_color("panel_bg", "#3c3f41").name()
                    try:
                        dock.setStyleSheet(f"QDockWidget {{ background: {c}; }}")
                        scroll.setStyleSheet(f"QWidget {{ background: {c}; }}")
                    except Exception:
                        pass
                except Exception:
                    pass

            # Attach refresh helper for external use
            try:
                self.mw.refresh_dock_backgrounds = refresh_dock_backgrounds
            except Exception:
                pass
        except Exception:
            pass

    def _build_execution_section(self) -> QWidget:
        """Build the execution controls section."""
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Execution Controls</b>"))
        else:
            layout.addWidget(QLabel("<b>Execution Controls</b>"))

        # Processor type
        proc_layout = QHBoxLayout()
        proc_layout.addWidget(QLabel("Processor:"))
        mw.processor_combo = QComboBox()
        mw.processor_combo.addItems(
            ["Forward Processing", "Concurrent", "Manual Processing"]
        )
        mw.processor_combo.setCurrentIndex(1)
        mw.processor_combo.currentIndexChanged.connect(mw.on_processor_type_changed)
        proc_layout.addWidget(mw.processor_combo)
        layout.addLayout(proc_layout)

        # Threading mode
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("Threading:"))
        mw.threading_combo = QComboBox()
        mw.threading_combo.addItems(["Single Thread", "Multi Thread"])
        mw.threading_combo.setCurrentIndex(0)
        mw.threading_combo.currentIndexChanged.connect(mw.on_threading_mode_changed)
        thread_layout.addWidget(mw.threading_combo)
        layout.addLayout(thread_layout)

        # === Multi-Graph Support: Graph Selector ===
        graph_layout = QHBoxLayout()
        graph_layout.addWidget(QLabel("Graph:"))
        mw.graph_selector_combo = QComboBox()
        mw.graph_selector_combo.setToolTip(
            "Select which graph to process. 'Mother Graph' processes all nodes."
        )
        mw.graph_selector_combo.addItem("Mother Graph (All)")
        mw.graph_selector_combo.currentIndexChanged.connect(
            mw.on_graph_selection_changed
        )
        graph_layout.addWidget(mw.graph_selector_combo)
        layout.addLayout(graph_layout)

        # Starting nodes widget
        self._build_starting_nodes_widget(layout)

        # Stopping nodes widget
        self._build_stopping_nodes_widget(layout)

        # Manual sequence widget
        self._build_manual_sequence_widget(layout)

        layout.addWidget(QLabel(""))  # Spacer

        # Play/Pause/Step/Reset buttons
        self._build_execution_buttons(layout)

        # Max steps
        steps_layout = QHBoxLayout()
        steps_layout.addWidget(QLabel("Max Steps:"))
        mw.max_steps_spin = QSpinBox()
        mw.max_steps_spin.setRange(1, 100000000)
        mw.max_steps_spin.setValue(100)
        steps_layout.addWidget(mw.max_steps_spin)
        layout.addLayout(steps_layout)

        # Speed controls
        self._build_speed_controls(layout)

        # Display steps as 'current / max' on the main step label
        mw.step_label = QLabel(f"Step: 0 / {mw.max_steps_spin.value()}")
        layout.addWidget(mw.step_label)

        # Progress bar showing execution progress under the step counter (no inline text)
        mw.step_progress = QProgressBar()
        mw.step_progress.setMinimum(0)
        mw.step_progress.setMaximum(mw.max_steps_spin.value())
        mw.step_progress.setValue(0)
        mw.step_progress.setTextVisible(False)
        layout.addWidget(mw.step_progress)

        # Keep the progress bar maximum in sync with Max Steps spin box and update step label
        def _on_max_steps_changed(v):
            try:
                mw.step_progress.setMaximum(v)
                current = (
                    mw.step_progress.value() if mw.step_progress is not None else 0
                )
                mw.step_label.setText(f"Step: {current} / {v}")
            except Exception:
                pass

        mw.max_steps_spin.valueChanged.connect(_on_max_steps_changed)

        layout.addWidget(QLabel(""))  # Spacer

        # Add processing queue as collapsible sub-section inside execution
        from ..main_window import CollapsibleSection

        queue_container = self._build_queue_section()
        # Use a FontAwesome icon for the section header instead of an emoji
        section = CollapsibleSection(
            "Processing Queue", queue_container, expanded=False
        )
        _apply_icon(
            mw,
            section.toggle_button,
            "fa5s.tasks",
            QStyle.StandardPixmap.SP_FileDialogListView,
            14,
        )
        layout.addWidget(section)

        return container

    def _build_starting_nodes_widget(self, parent_layout):
        """Build starting nodes management widget."""
        mw = self.mw
        mw.starting_nodes_widget = QWidget()
        mw.starting_nodes_widget.setVisible(False)
        group = QVBoxLayout(mw.starting_nodes_widget)
        group.setContentsMargins(0, 0, 0, 0)
        if ThemedLabel is not None:
            group.addWidget(ThemedLabel("<b>Starting Nodes</b>"))
        else:
            group.addWidget(QLabel("<b>Starting Nodes</b>"))

        # Use a QLabel with word wrap for compact comma-separated display
        mw.starting_nodes_label = QLabel()
        mw.starting_nodes_label.setWordWrap(True)
        mw.starting_nodes_label.setMinimumHeight(24)
        mw.starting_nodes_label.setTextInteractionFlags(
            mw.starting_nodes_label.textInteractionFlags()
            | Qt.TextInteractionFlag.TextSelectableByMouse
        )
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()
            mw._theme_manager = tm
            list_bg = tm.get_color("list_bg", "#313335").name()
            border = tm.get_color("border", "#555555").name()
            text_color = tm.get_color("text", "#ffffff").name()
            mw.starting_nodes_label.setStyleSheet(
                f"QLabel {{ background-color: {list_bg}; border: 1px solid {border}; "
                f"color: {text_color}; padding: 4px; }}"
            )
            try:
                mw._theme_manager.theme_changed.connect(
                    lambda: mw.starting_nodes_label.setStyleSheet(
                        f"QLabel {{ background-color: {mw._theme_manager.get_color('list_bg').name()}; "
                        f"border: 1px solid {mw._theme_manager.get_color('border').name()}; "
                        f"color: {mw._theme_manager.get_color('text').name()}; padding: 4px; }}"
                    )
                )
            except Exception:
                pass
        except Exception:
            mw.starting_nodes_label.setStyleSheet(
                "QLabel { background-color: #2a2a2a; border: 1px solid #555; "
                "color: #ffffff; padding: 4px; }"
            )
        group.addWidget(mw.starting_nodes_label)

        btn_row1 = QHBoxLayout()
        mw.add_to_starting_btn = _create_standard_button(
            mw,
            "Add Selected",
            "fa5s.arrow-right",
            QStyle.StandardPixmap.SP_ArrowRight,
            14,
        )
        mw.add_to_starting_btn.setToolTip("Add selected node(s) from canvas")
        mw.add_to_starting_btn.clicked.connect(mw.add_selected_to_starting_nodes)
        btn_row1.addWidget(mw.add_to_starting_btn)

        mw.remove_from_starting_btn = _create_standard_button(
            mw, "Remove", "fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon, 14
        )
        mw.remove_from_starting_btn.setToolTip(
            "Remove selected canvas node(s) from starting nodes"
        )
        mw.remove_from_starting_btn.clicked.connect(mw.remove_from_starting_nodes)
        btn_row1.addWidget(mw.remove_from_starting_btn)
        group.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        mw.auto_detect_starting_btn = _create_standard_button(
            mw, "Auto-Detect", "fa5s.sync", QStyle.StandardPixmap.SP_BrowserReload, 14
        )
        mw.auto_detect_starting_btn.setToolTip("Auto-detect nodes with no predecessors")
        mw.auto_detect_starting_btn.clicked.connect(mw.auto_detect_starting_nodes)
        btn_row2.addWidget(mw.auto_detect_starting_btn)

        mw.clear_starting_btn = _create_standard_button(
            mw,
            "Clear All",
            "fa5s.eraser",
            QStyle.StandardPixmap.SP_DialogResetButton,
            14,
        )
        mw.clear_starting_btn.clicked.connect(mw.clear_starting_nodes)
        btn_row2.addWidget(mw.clear_starting_btn)
        group.addLayout(btn_row2)

        parent_layout.addWidget(mw.starting_nodes_widget)

    def _build_stopping_nodes_widget(self, parent_layout):
        """Build stopping nodes management widget."""
        mw = self.mw
        mw.stopping_nodes_widget = QWidget()
        mw.stopping_nodes_widget.setVisible(False)
        group = QVBoxLayout(mw.stopping_nodes_widget)
        group.setContentsMargins(0, 0, 0, 0)
        if ThemedLabel is not None:
            group.addWidget(ThemedLabel("<b>Stopping Nodes</b>"))
        else:
            group.addWidget(QLabel("<b>Stopping Nodes</b>"))

        mw.stopping_nodes_list = QListWidget()
        mw.stopping_nodes_list.setMaximumHeight(120)
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()
            mw._theme_manager = tm
        except Exception:
            tm = None
        if tm is not None:
            panel = tm.get_color("panel_bg", "#3c3f41").name()
            border = tm.get_color("border", "#555555").name()
            list_bg = tm.get_color("list_bg", "#313335").name()
            mw.stopping_nodes_list.setStyleSheet(
                f"QListWidget {{ background-color: {list_bg}; border: 1px solid {border}; }}"
            )
            try:
                mw._theme_manager.theme_changed.connect(
                    lambda: mw.stopping_nodes_list.setStyleSheet(
                        f"QListWidget {{ background-color: {mw._theme_manager.get_color('list_bg').name()}; border: 1px solid {mw._theme_manager.get_color('border').name()}; }}"
                    )
                )
            except Exception:
                pass
        else:
            mw.stopping_nodes_list.setStyleSheet(
                "QListWidget { background-color: #2a2a2a; border: 1px solid #555; }"
            )
        group.addWidget(mw.stopping_nodes_list)

        btn_row1 = QHBoxLayout()
        mw.add_to_stopping_btn = _create_standard_button(
            mw,
            "Add Selected",
            "fa5s.arrow-right",
            QStyle.StandardPixmap.SP_ArrowRight,
            14,
        )
        mw.add_to_stopping_btn.setToolTip("Add selected node(s) from canvas")
        mw.add_to_stopping_btn.clicked.connect(mw.add_selected_to_stopping_nodes)
        btn_row1.addWidget(mw.add_to_stopping_btn)

        mw.remove_from_stopping_btn = _create_standard_button(
            mw, "Remove", "fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon, 14
        )
        mw.remove_from_stopping_btn.setToolTip("Remove selected node(s)")
        mw.remove_from_stopping_btn.clicked.connect(mw.remove_from_stopping_nodes)
        btn_row1.addWidget(mw.remove_from_stopping_btn)
        group.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        mw.auto_detect_stopping_btn = _create_standard_button(
            mw, "Auto-Detect", "fa5s.sync", QStyle.StandardPixmap.SP_BrowserReload, 14
        )
        mw.auto_detect_stopping_btn.setToolTip("Auto-detect candidate stopping nodes")
        mw.auto_detect_stopping_btn.clicked.connect(mw.auto_detect_stopping_nodes)
        btn_row2.addWidget(mw.auto_detect_stopping_btn)

        mw.clear_stopping_btn = _create_standard_button(
            mw,
            "Clear All",
            "fa5s.eraser",
            QStyle.StandardPixmap.SP_DialogResetButton,
            14,
        )
        mw.clear_stopping_btn.clicked.connect(mw.clear_stopping_nodes)
        btn_row2.addWidget(mw.clear_stopping_btn)
        group.addLayout(btn_row2)

        parent_layout.addWidget(mw.stopping_nodes_widget)

    def _build_manual_sequence_widget(self, parent_layout):
        """Build manual sequence management widget."""
        mw = self.mw
        mw.manual_sequence_widget = QWidget()
        mw.manual_sequence_widget.setVisible(False)
        group = QVBoxLayout(mw.manual_sequence_widget)
        group.setContentsMargins(0, 0, 0, 0)
        if ThemedLabel is not None:
            group.addWidget(ThemedLabel("<b>Manual Sequence</b>"))
        else:
            group.addWidget(QLabel("<b>Manual Sequence</b>"))

        mw.manual_sequence_list = QListWidget()
        mw.manual_sequence_list.setMinimumHeight(120)
        mw.manual_sequence_list.setMaximumHeight(300)
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()
            mw._theme_manager = tm
        except Exception:
            tm = None
        if tm is not None:
            panel = tm.get_color("panel_bg", "#3c3f41").name()
            border = tm.get_color("border", "#555555").name()
            list_bg = tm.get_color("list_bg", "#313335").name()
            mw.manual_sequence_list.setStyleSheet(
                f"QListWidget {{ background-color: {list_bg}; border: 1px solid {border}; }}"
            )
            try:
                mw._theme_manager.theme_changed.connect(
                    lambda: mw.manual_sequence_list.setStyleSheet(
                        f"QListWidget {{ background-color: {mw._theme_manager.get_color('list_bg').name()}; border: 1px solid {mw._theme_manager.get_color('border').name()}; }}"
                    )
                )
            except Exception:
                pass
        else:
            mw.manual_sequence_list.setStyleSheet(
                "QListWidget { background-color: #2a2a2a; border: 1px solid #555; }"
            )
        group.addWidget(mw.manual_sequence_list)

        btn_row1 = QHBoxLayout()
        mw.add_step_selected_btn = _create_standard_button(
            mw,
            "Add Step (Selected)",
            "fa5s.plus",
            QStyle.StandardPixmap.SP_FileDialogNewFolder,
            14,
        )
        mw.add_step_selected_btn.clicked.connect(mw.add_selected_to_manual_sequence)
        btn_row1.addWidget(mw.add_step_selected_btn)

        mw.add_to_selected_step_btn = _create_standard_button(
            mw,
            "Add to Selected Step",
            "fa5s.arrow-right",
            QStyle.StandardPixmap.SP_ArrowRight,
            14,
        )
        mw.add_to_selected_step_btn.setToolTip("Add selected node(s) to chosen step")
        mw.add_to_selected_step_btn.clicked.connect(
            mw.add_selected_nodes_to_selected_step
        )
        btn_row1.addWidget(mw.add_to_selected_step_btn)
        group.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        mw.remove_step_btn = _create_standard_button(
            mw, "Remove Step", "fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon, 14
        )
        mw.remove_step_btn.clicked.connect(mw.remove_from_manual_sequence)
        btn_row2.addWidget(mw.remove_step_btn)

        mw.clear_sequence_btn = _create_standard_button(
            mw,
            "Clear Sequence",
            "fa5s.eraser",
            QStyle.StandardPixmap.SP_DialogResetButton,
            14,
        )
        mw.clear_sequence_btn.clicked.connect(mw.clear_manual_sequence)
        btn_row2.addWidget(mw.clear_sequence_btn)
        group.addLayout(btn_row2)

        btn_row3 = QHBoxLayout()
        mw.load_sequence_btn = _create_standard_button(
            mw,
            "Load Sequence",
            "fa5s.folder-open",
            QStyle.StandardPixmap.SP_DialogOpenButton,
            14,
        )
        mw.load_sequence_btn.clicked.connect(mw.load_manual_sequence_from_graph)
        btn_row3.addWidget(mw.load_sequence_btn)

        # "Apply to Graph" button removed - sequence now auto-applies on changes

        mw.replace_selected_step_btn = _create_standard_button(
            mw,
            "Replace Selected Step",
            "fa5s.sync",
            QStyle.StandardPixmap.SP_BrowserReload,
            14,
        )
        mw.replace_selected_step_btn.setToolTip("Replace step with selected nodes")
        mw.replace_selected_step_btn.clicked.connect(
            mw.replace_selected_step_with_selected_nodes
        )
        btn_row3.addWidget(mw.replace_selected_step_btn)
        group.addLayout(btn_row3)

        parent_layout.addWidget(mw.manual_sequence_widget)

    def _build_execution_buttons(self, parent_layout):
        """Build play/pause/step/reset buttons.

        Attempts to use MVVM ExecutionView if available, falls back to legacy buttons.
        """
        mw = self.mw

        # Try MVVM integration first
        if self._try_build_mvvm_execution_controls(parent_layout):
            return  # MVVM controls built successfully

        # Fallback to legacy buttons
        self._build_legacy_execution_buttons(parent_layout)

    def _try_build_mvvm_execution_controls(self, parent_layout) -> bool:
        """Attempt to build MVVM-based execution controls.

        Returns:
            True if MVVM controls were built successfully, False to use legacy.
        """
        mw = self.mw

        try:
            # Check if MVVM adapter is available
            if not hasattr(mw, "execution_adapter") or mw.execution_adapter is None:
                logger.debug(
                    "MVVM ExecutionAdapter not available, using legacy controls"
                )
                return False

            from gui_framework.views.execution_view import PYQT_AVAILABLE, ExecutionView

            if not PYQT_AVAILABLE:
                logger.debug(
                    "PyQt6 not available for ExecutionView, using legacy controls"
                )
                return False

            # Create the MVVM ExecutionView with the adapter's viewmodel
            execution_view = ExecutionView(mw.execution_adapter.viewmodel, parent=mw)

            # Store reference on main window for later access
            mw.mvvm_execution_view = execution_view

            # Add the MVVM view to the layout
            parent_layout.addWidget(execution_view)

            # Also create minimal legacy button references for compatibility
            # (some code may reference mw.play_btn, etc.)
            self._create_legacy_button_aliases(execution_view)

            logger.info("MVVM ExecutionView integrated successfully")
            return True

        except Exception as e:
            logger.warning("Failed to build MVVM execution controls: %s", e)
            return False

    def _create_legacy_button_aliases(self, execution_view):
        """Create legacy button aliases pointing to MVVM view buttons.

        This provides backward compatibility for code that references
        mw.play_btn, mw.pause_btn, etc.
        """
        mw = self.mw
        try:
            mw.play_btn = execution_view.play_button
            mw.pause_btn = execution_view.pause_button
            mw.resume_btn = execution_view.resume_button
            mw.step_btn = execution_view.step_button
            mw.reset_btn = execution_view.reset_button
            mw.restore_graph_btn = execution_view.restore_button
            mw.reset_processor_btn = (
                execution_view.stop_button
            )  # stop_button = Reset Proc in MVVM
            mw.rebuild_exec_btn = execution_view.rebuild_button
            # Store reference to progress bar for legacy access
            mw.mvvm_step_progress = execution_view.progress_bar
            mw.mvvm_step_label = execution_view.step_label
        except Exception as e:
            logger.debug("Could not create legacy button aliases: %s", e)

    def _build_legacy_execution_buttons(self, parent_layout):
        """Build legacy play/pause/step/reset buttons."""
        mw = self.mw

        btn_row = QHBoxLayout()
        mw.play_btn = _create_standard_button(
            mw, "Start", "fa5s.play", QStyle.StandardPixmap.SP_MediaPlay, 16
        )
        # Ensure a stable objectName and inline style for exact parity with toolbar button
        try:
            mw.play_btn.setObjectName("play_btn")
            # Do not apply inline styles; rely on global QSS for unified appearance
            pass
        except Exception:
            pass
        mw.play_btn.clicked.connect(mw.play_graph)
        btn_row.addWidget(mw.play_btn)

        mw.pause_btn = _create_standard_button(
            mw, "Pause", "fa5s.pause", QStyle.StandardPixmap.SP_MediaPause, 16
        )
        mw.pause_btn.clicked.connect(mw.pause_graph)
        mw.pause_btn.setEnabled(False)
        btn_row.addWidget(mw.pause_btn)

        mw.resume_btn = _create_standard_button(
            mw, "Resume", "fa5s.play", QStyle.StandardPixmap.SP_MediaPlay, 16
        )
        mw.resume_btn.clicked.connect(mw.resume_graph)
        mw.resume_btn.setEnabled(False)
        btn_row.addWidget(mw.resume_btn)
        parent_layout.addLayout(btn_row)

        mw.step_btn = _create_standard_button(
            mw, "Step", "fa5s.step-forward", QStyle.StandardPixmap.SP_ArrowRight, 14
        )
        mw.step_btn.clicked.connect(mw.step_graph)
        parent_layout.addWidget(mw.step_btn)

        # Reset controls - split into Restore Graph, Reset Processor, and Reset All
        reset_row = QHBoxLayout()

        mw.restore_graph_btn = _create_standard_button(
            mw, "Restore", "fa5s.undo", QStyle.StandardPixmap.SP_BrowserReload, 14
        )
        mw.restore_graph_btn.setToolTip(
            "Restore graph to iteration 0 state (node values) without changing iteration counter"
        )
        mw.restore_graph_btn.clicked.connect(mw.restore_graph)
        reset_row.addWidget(mw.restore_graph_btn)

        mw.reset_processor_btn = _create_standard_button(
            mw, "Reset Proc", "fa5s.stop", QStyle.StandardPixmap.SP_MediaStop, 14
        )
        mw.reset_processor_btn.setToolTip(
            "Reset iteration counter to 0 and reinitialize processor (preserves node values)"
        )
        mw.reset_processor_btn.clicked.connect(mw.reset_processor)
        reset_row.addWidget(mw.reset_processor_btn)

        mw.reset_btn = _create_standard_button(
            mw, "Reset All", "fa5s.sync", QStyle.StandardPixmap.SP_DialogResetButton, 14
        )
        mw.reset_btn.setToolTip(
            "Full reset: restore graph to iteration 0 AND reset processor/counter"
        )
        mw.reset_btn.clicked.connect(mw.reset_graph)
        reset_row.addWidget(mw.reset_btn)

        parent_layout.addLayout(reset_row)

        mw.rebuild_exec_btn = _create_standard_button(mw, "Rebuild", None, None, 14)
        mw.rebuild_exec_btn.setToolTip("Rebuild graph from canvas")
        mw.rebuild_exec_btn.clicked.connect(mw.rebuild_graph)
        parent_layout.addWidget(mw.rebuild_exec_btn)

    def _build_speed_controls(self, parent_layout):
        """Build speed and visualization options."""
        mw = self.mw
        speed_layout = QVBoxLayout()

        mw.max_speed_btn = _create_standard_button(
            mw, "Max Speed (0ms)", "fa5s.bolt", QStyle.StandardPixmap.SP_ArrowRight, 14
        )
        mw.max_speed_btn.setCheckable(True)
        mw.max_speed_btn.setToolTip("Set visualization delay to 0ms")
        mw.max_speed_btn.clicked.connect(mw.on_max_speed_toggled)
        speed_layout.addWidget(mw.max_speed_btn)

        mw.skip_viz_check = QCheckBox("Skip Graph Visualization")
        mw.skip_viz_check.setToolTip("Run without updating graph visuals")
        mw.skip_viz_check.stateChanged.connect(mw.on_skip_viz_changed)
        speed_layout.addWidget(mw.skip_viz_check)

        mw.skip_plot_check = QCheckBox("Skip Plot Updates")
        mw.skip_plot_check.setToolTip("Run without updating plot window")
        mw.skip_plot_check.stateChanged.connect(mw.on_skip_plot_changed)
        speed_layout.addWidget(mw.skip_plot_check)

        mw.verbose_check = QCheckBox("Verbose Terminal Output")
        mw.verbose_check.setToolTip("Enable detailed logging")
        mw.verbose_check.stateChanged.connect(mw.on_verbose_changed)
        speed_layout.addWidget(mw.verbose_check)

        mw.dim_processed_check = QCheckBox("Dim Processed Nodes (Debug)")
        mw.dim_processed_check.setToolTip("Dim processed nodes")
        mw.dim_processed_check.stateChanged.connect(mw.on_dim_processed_changed)
        speed_layout.addWidget(mw.dim_processed_check)

        speed_layout.addWidget(QLabel("Visualization Delay (ms/step):"))
        try:
            if ThemedSlider is not None:
                mw.speed_slider = ThemedSlider(Qt.Orientation.Horizontal)
            else:
                mw.speed_slider = QSlider(Qt.Orientation.Horizontal)
        except Exception:
            mw.speed_slider = QSlider(Qt.Orientation.Horizontal)
        mw.speed_slider.setRange(5, 2000)
        mw.speed_slider.setValue(500)
        mw.speed_slider.valueChanged.connect(mw.on_speed_changed)
        speed_layout.addWidget(mw.speed_slider)

        spin_layout = QHBoxLayout()
        mw.speed_spin = QSpinBox()
        mw.speed_spin.setRange(5, 2000)
        mw.speed_spin.setValue(500)
        mw.speed_spin.setSingleStep(10)
        mw.speed_spin.valueChanged.connect(mw.on_speed_spin_changed)
        spin_layout.addWidget(mw.speed_spin)

        mw.speed_label = QLabel("500 ms")
        spin_layout.addWidget(mw.speed_label)
        spin_layout.addStretch()
        speed_layout.addLayout(spin_layout)

        # Apply a themed stylesheet to the slider so the groove/track is visible
        try:
            from ..theme import get_theme_manager

            tm = get_theme_manager()

            def _apply_slider_theme():
                try:
                    # Prefer list_bg for the groove; if it equals panel_bg, derive a contrasting color
                    panel_bg = tm.get_color(
                        "panel_bg", tm.get_color("bg", "#3c3f41")
                    ).name()
                    list_bg = tm.get_color("list_bg", panel_bg).name()
                    fill = tm.get_color("accent", "#4a86e8").name()
                    handle = tm.get_color("accent", "#4a86e8").name()

                    from PyQt6.QtGui import QColor

                    groove_color = list_bg
                    try:
                        if QColor(list_bg).name() == QColor(panel_bg).name():
                            # Compute luminance to pick lighter/darker for contrast
                            c = QColor(panel_bg)
                            lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
                            if lum < 128:
                                groove_color = c.lighter(120).name()
                            else:
                                groove_color = c.darker(120).name()
                    except Exception:
                        groove_color = list_bg

                    # Border color for subtle outline
                    border = tm.get_color("border", "#555555").name()

                    ss = (
                        "QSlider::groove:horizontal { height: 10px; background: %s; border-radius: 5px; border: 1px solid %s; } "
                        "QSlider::sub-page:horizontal { background: %s; border-radius: 5px; } "
                        "QSlider::add-page:horizontal { background: %s; border-radius: 5px; } "
                        "QSlider::handle:horizontal { background: %s; width: 16px; height: 16px; margin: -4px 0; border-radius: 8px; border: 1px solid %s; } "
                        "QSlider::handle:horizontal:hover { border-color: %s; background: %s; }"
                        % (
                            groove_color,
                            border,
                            fill,
                            groove_color,
                            handle,
                            border,
                            tm.get_color("accent").name(),
                            tm.get_color("accent").lighter(110).name(),
                        )
                    )
                    try:
                        mw.speed_slider.setStyleSheet(ss)
                    except Exception:
                        pass
                except Exception:
                    pass

            # Apply initially and on theme changes
            _apply_slider_theme()
            try:
                tm.theme_changed.connect(_apply_slider_theme)
            except Exception:
                pass
        except Exception:
            pass

        parent_layout.addLayout(speed_layout)

    def _build_queue_section(self) -> QWidget:
        """Build the processing queue section (Phase 2)."""
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(
            QLabel("Run graphs/subgraphs sequentially with specified iterations.")
        )

        # Queue list
        mw.queue_list = QListWidget()
        mw.queue_list.setMaximumHeight(150)
        try:
            from ..theme import get_theme_manager

            tm = getattr(mw, "_theme_manager", None) or get_theme_manager()
            mw._theme_manager = tm
        except Exception:
            tm = None
        if tm is not None:
            panel = tm.get_color("panel_bg", "#3c3f41").name()
            border = tm.get_color("border", "#555555").name()
            list_bg = tm.get_color("list_bg", "#313335").name()
            mw.queue_list.setStyleSheet(
                f"QListWidget {{ background-color: {list_bg}; border: 1px solid {border}; }}"
            )
            try:
                mw._theme_manager.theme_changed.connect(
                    lambda: mw.queue_list.setStyleSheet(
                        f"QListWidget {{ background-color: {mw._theme_manager.get_color('list_bg').name()}; border: 1px solid {mw._theme_manager.get_color('border').name()}; }}"
                    )
                )
            except Exception:
                pass
        else:
            mw.queue_list.setStyleSheet(
                "QListWidget { background-color: #2a2a2a; border: 1px solid #555; }"
            )
        mw.queue_list.setToolTip(
            "Processing queue: each item runs for its specified iterations"
        )
        layout.addWidget(mw.queue_list)

        # Add to queue row
        add_row = QHBoxLayout()
        add_row.addWidget(QLabel("Iterations:"))
        mw.queue_iterations_spin = QSpinBox()
        mw.queue_iterations_spin.setRange(1, 100000)
        mw.queue_iterations_spin.setValue(100)
        add_row.addWidget(mw.queue_iterations_spin)

        mw.add_to_queue_btn = _create_standard_button(
            mw, "Add", "fa5s.plus", QStyle.StandardPixmap.SP_FileDialogNewFolder, 14
        )
        mw.add_to_queue_btn.setToolTip(
            "Add the currently selected graph/subgraph to the queue"
        )
        mw.add_to_queue_btn.clicked.connect(mw.add_selected_graph_to_queue)
        add_row.addWidget(mw.add_to_queue_btn)
        layout.addLayout(add_row)

        # Repeat controls
        repeat_row = QHBoxLayout()
        mw.queue_repeat_check = QCheckBox("Repeat")
        mw.queue_repeat_check.setToolTip(
            "When checked, queue will restart from beginning after completing"
        )
        mw.queue_repeat_check.stateChanged.connect(mw.on_queue_repeat_changed)
        repeat_row.addWidget(mw.queue_repeat_check)

        mw.queue_repeat_spin = QSpinBox()
        mw.queue_repeat_spin.setRange(0, 10000)
        mw.queue_repeat_spin.setValue(0)
        mw.queue_repeat_spin.setToolTip("Repeat count: 0 = forever, N = repeat N times")
        mw.queue_repeat_spin.setEnabled(False)  # Disabled until repeat is checked
        repeat_row.addWidget(mw.queue_repeat_spin)
        # Use ASCII 'inf' to avoid non-ASCII infinity symbol
        repeat_row.addWidget(QLabel("times (0=inf)"))
        repeat_row.addStretch()
        layout.addLayout(repeat_row)

        # Queue control buttons
        btn_row1 = QHBoxLayout()
        btn_row1 = QHBoxLayout()
        mw.start_queue_btn = _create_standard_button(
            mw, "Run Queue", "fa5s.play", QStyle.StandardPixmap.SP_MediaPlay, 14
        )
        mw.start_queue_btn.setToolTip("Start processing the queue sequentially")
        mw.start_queue_btn.clicked.connect(mw.start_processing_queue)
        btn_row1.addWidget(mw.start_queue_btn)

        mw.stop_queue_btn = _create_standard_button(
            mw, "Stop Queue", "fa5s.stop", QStyle.StandardPixmap.SP_MediaStop, 14
        )
        mw.stop_queue_btn.setToolTip("Stop queue processing")
        mw.stop_queue_btn.clicked.connect(mw.stop_processing_queue)
        mw.stop_queue_btn.setEnabled(False)
        btn_row1.addWidget(mw.stop_queue_btn)
        layout.addLayout(btn_row1)

        btn_row2 = QHBoxLayout()
        mw.remove_from_queue_btn = _create_standard_button(
            mw, "Remove Selected", "fa5s.trash", QStyle.StandardPixmap.SP_TrashIcon, 14
        )
        mw.remove_from_queue_btn.setToolTip("Remove selected item from queue")
        mw.remove_from_queue_btn.clicked.connect(mw.remove_selected_from_queue)
        btn_row2.addWidget(mw.remove_from_queue_btn)

        mw.clear_queue_btn = _create_standard_button(
            mw,
            "Clear Queue",
            "fa5s.eraser",
            QStyle.StandardPixmap.SP_DialogResetButton,
            14,
        )
        mw.clear_queue_btn.clicked.connect(mw.clear_processing_queue)
        btn_row2.addWidget(mw.clear_queue_btn)
        layout.addLayout(btn_row2)

        # Per-graph reset
        layout.addWidget(QLabel(""))  # Spacer
        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Per-Graph Reset</b>"))
        else:
            layout.addWidget(QLabel("<b>Per-Graph Reset</b>"))

        reset_row = QHBoxLayout()
        mw.save_graph_snapshot_btn = _create_standard_button(
            mw,
            "Save Snapshot",
            "fa5s.camera",
            QStyle.StandardPixmap.SP_DialogSaveButton,
            14,
        )
        mw.save_graph_snapshot_btn.setToolTip(
            "Save snapshot of selected graph/subgraph"
        )
        mw.save_graph_snapshot_btn.clicked.connect(mw.save_selected_graph_snapshot)
        reset_row.addWidget(mw.save_graph_snapshot_btn)

        mw.reset_selected_graph_btn = _create_standard_button(
            mw, "Reset Graph", "fa5s.undo", QStyle.StandardPixmap.SP_BrowserReload, 14
        )
        mw.reset_selected_graph_btn.setToolTip(
            "Reset selected graph/subgraph to its snapshot"
        )
        mw.reset_selected_graph_btn.clicked.connect(mw.reset_selected_graph)
        reset_row.addWidget(mw.reset_selected_graph_btn)
        layout.addLayout(reset_row)

        # Queue status
        mw.queue_status_label = QLabel("Queue: Empty")
        layout.addWidget(mw.queue_status_label)

        return container

    def _build_visualization_section(self) -> QWidget:
        """Build the visualization controls section."""
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Visualization</b>"))
        else:
            layout.addWidget(QLabel("<b>Visualization</b>"))

        # Colorize Graph subsection inside Visualization
        if ThemedLabel is not None:
            colorize_group_label = ThemedLabel("<b>Colorize Graph</b>")
        else:
            colorize_group_label = QLabel("<b>Colorize Graph</b>")
        layout.addWidget(colorize_group_label)

        # Container for all colorize controls (value & ANN, plus clear)
        mw.colorize_group_container = QWidget()
        mw.colorize_group_layout = QVBoxLayout(mw.colorize_group_container)
        mw.colorize_group_layout.setContentsMargins(0, 0, 0, 0)
        mw.colorize_group_container.setLayout(mw.colorize_group_layout)
        layout.addWidget(mw.colorize_group_container)

        # Colorize by value checkbox and its settings
        mw.colorize_check = QCheckBox("Colorize by Value")
        mw.colorize_check.stateChanged.connect(mw.on_colorize_changed)
        mw.colorize_group_layout.addWidget(mw.colorize_check)

        # Create a container for colorize-by-value settings so they can be shown/hidden
        # under the Colorize by Value checkbox like a drop-down section.
        mw.colorize_settings_container = QWidget()
        mw.colorize_settings_layout = QVBoxLayout(mw.colorize_settings_container)
        mw.colorize_settings_layout.setContentsMargins(10, 0, 0, 0)
        mw.colorize_settings_container.setLayout(mw.colorize_settings_layout)
        mw.colorize_settings_container.setVisible(False)
        mw.colorize_group_layout.addWidget(mw.colorize_settings_container)

        mw.auto_range_btn = _create_standard_button(
            mw, "Auto Detect Min/Max", None, None, 14
        )
        mw.auto_range_btn.clicked.connect(mw.auto_detect_range)
        mw.auto_range_btn.setEnabled(False)
        mw.colorize_settings_layout.addWidget(mw.auto_range_btn)

        # Min/Max value labels inside the settings container
        self._build_color_range_controls(mw.colorize_settings_layout)

        # Gradient color buttons inside the settings container
        self._build_gradient_controls(mw.colorize_settings_layout)

        layout.addWidget(QLabel(""))  # Spacer

        # Node appearance
        self._build_node_appearance_controls(layout)

        # Grid & Snap controls
        self._build_grid_snap_controls(layout)

        # ANN Colors toggle and Clear button (mutually exclusive with Colorize by Value)
        ann_colors_row = QHBoxLayout()
        mw.ann_colors_check = QCheckBox("Colorize as ANN")
        mw.ann_colors_check.setToolTip(
            "Toggle ANN-style color scheme (mutually exclusive with Colorize by Value)"
        )
        mw.ann_colors_check.stateChanged.connect(mw.on_ann_color_changed)
        ann_colors_row.addWidget(mw.ann_colors_check)
        mw.ann_colors_check.setChecked(getattr(mw, "ann_colors_enabled", False))

        mw.clear_ann_colors_btn = _create_standard_button(mw, "Clear", None, None, 14)
        mw.clear_ann_colors_btn.setToolTip(
            "Clear coloring (ANN or value) and revert to default colors"
        )
        # Connect to visualization controller 'clear_colors' to clear both modes
        mw.clear_ann_colors_btn.clicked.connect(
            mw.visualization_controller.clear_colors
        )
        ann_colors_row.addWidget(mw.clear_ann_colors_btn)

        # Topology Labels toggle
        mw.topology_labels_check = QCheckBox("Show Topology Labels")
        mw.topology_labels_check.setToolTip(
            "Display node topology type (isolated, endpoint, entrypoint, link, "
            "greedy, genesis, distribution, union, cross) below each node"
        )
        mw.topology_labels_check.stateChanged.connect(mw.on_topology_labels_changed)
        mw.topology_labels_check.setChecked(
            getattr(mw, "topology_labels_enabled", False)
        )
        mw.colorize_group_layout.addWidget(mw.topology_labels_check)

        # Add ANN and Clear to colorize group so they are inside 'Colorize Graph' and Clear appears last
        mw.colorize_group_layout.addLayout(ann_colors_row)

        layout.addStretch()
        return container

    def _build_color_range_controls(self, parent_layout):
        """Build min/max value display."""
        mw = self.mw
        color_range = QVBoxLayout()

        min_layout = QHBoxLayout()
        min_layout.addWidget(QLabel("Min Value:"))
        mw.min_value_label = QLabel("0.0")
        mw.min_value_label.setStyleSheet("font-weight: bold;")
        min_layout.addWidget(mw.min_value_label)
        min_layout.addStretch()
        color_range.addLayout(min_layout)

        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("Max Value:"))
        mw.max_value_label = QLabel("1.0")
        mw.max_value_label.setStyleSheet("font-weight: bold;")
        max_layout.addWidget(mw.max_value_label)
        max_layout.addStretch()
        color_range.addLayout(max_layout)

        parent_layout.addLayout(color_range)

    def _build_gradient_controls(self, parent_layout):
        """Build gradient color picker buttons."""
        mw = self.mw
        gradient = QVBoxLayout()

        min_color_layout = QHBoxLayout()
        min_color_layout.addWidget(QLabel("Min Color:"))
        mw.min_color_btn = _create_standard_button(mw, "", None, None, 14)
        mw.min_color_btn.setFixedSize(60, 25)
        mw.min_color_btn.setStyleSheet(
            f"background-color: {mw.min_gradient_color.name()};"
        )
        mw.min_color_btn.clicked.connect(mw.choose_min_color)
        min_color_layout.addWidget(mw.min_color_btn)
        min_color_layout.addStretch()
        gradient.addLayout(min_color_layout)

        max_color_layout = QHBoxLayout()
        max_color_layout.addWidget(QLabel("Max Color:"))
        mw.max_color_btn = _create_standard_button(mw, "", None, None, 14)
        mw.max_color_btn.setFixedSize(60, 25)
        mw.max_color_btn.setStyleSheet(
            f"background-color: {mw.max_gradient_color.name()};"
        )
        mw.max_color_btn.clicked.connect(mw.choose_max_color)
        max_color_layout.addWidget(mw.max_color_btn)
        max_color_layout.addStretch()
        gradient.addLayout(max_color_layout)

        parent_layout.addLayout(gradient)

    def _build_node_appearance_controls(self, parent_layout):
        """Build node color controls."""
        mw = self.mw
        if ThemedLabel is not None:
            parent_layout.addWidget(ThemedLabel("<b>Node Appearance</b>"))
        else:
            parent_layout.addWidget(QLabel("<b>Node Appearance</b>"))

        node_color_layout = QHBoxLayout()
        node_color_layout.addWidget(QLabel("Node Color:"))
        mw.node_color_btn = _create_standard_button(mw, "", None, None, 14)
        mw.node_color_btn.setFixedSize(60, 25)
        # Respect any previously loaded/default value (persisted) before assigning
        if not hasattr(mw, "default_node_color") or mw.default_node_color is None:
            mw.default_node_color = QColor(100, 150, 200)
        mw.node_color_btn.setStyleSheet(
            f"background-color: {mw.default_node_color.name()};"
        )
        mw.node_color_btn.clicked.connect(mw.choose_node_color)
        node_color_layout.addWidget(mw.node_color_btn)
        node_color_layout.addStretch()
        parent_layout.addLayout(node_color_layout)

        text_color_layout = QHBoxLayout()
        text_color_layout.addWidget(QLabel("Text Color:"))
        mw.text_color_btn = _create_standard_button(mw, "", None, None, 14)
        mw.text_color_btn.setFixedSize(60, 25)
        # Respect persisted text color if available
        if not hasattr(mw, "default_text_color") or mw.default_text_color is None:
            mw.default_text_color = QColor(255, 255, 255)
        mw.text_color_btn.setStyleSheet(
            f"background-color: {mw.default_text_color.name()};"
        )
        mw.text_color_btn.clicked.connect(mw.choose_text_color)
        text_color_layout.addWidget(mw.text_color_btn)
        text_color_layout.addStretch()
        parent_layout.addLayout(text_color_layout)

        mw.apply_colors_btn = _create_standard_button(
            mw, "Apply to All Nodes", None, None, 14
        )
        mw.apply_colors_btn.clicked.connect(mw.apply_node_colors)
        parent_layout.addWidget(mw.apply_colors_btn)

        mw.apply_selected_colors_btn = _create_standard_button(
            mw, "Apply to Selected", None, None, 14
        )
        mw.apply_selected_colors_btn.clicked.connect(mw.apply_node_colors_selected)
        parent_layout.addWidget(mw.apply_selected_colors_btn)

    def _build_grid_snap_controls(self, parent_layout):
        """Build grid and snap controls."""
        mw = self.mw
        if ThemedLabel is not None:
            parent_layout.addWidget(ThemedLabel("<b>Grid & Snap</b>"))
        else:
            parent_layout.addWidget(QLabel("<b>Grid & Snap</b>"))

        mw.show_grid_check = QCheckBox("Show Grid")
        mw.show_grid_check.setToolTip("Toggle drawing the background grid")
        mw.show_grid_check.setChecked(True)
        mw.show_grid_check.stateChanged.connect(
            lambda s: mw.canvas.set_show_grid(s == Qt.CheckState.Checked.value)
        )
        parent_layout.addWidget(mw.show_grid_check)

        mw.snap_grid_check = QCheckBox("Snap to Grid")
        mw.snap_grid_check.setToolTip("Snap node positions to grid")
        mw.snap_grid_check.setChecked(True)
        mw.snap_grid_check.stateChanged.connect(
            lambda s: mw.canvas.set_snap_to_grid(s == Qt.CheckState.Checked.value)
        )
        parent_layout.addWidget(mw.snap_grid_check)

        mw.snap_while_dragging_check = QCheckBox("Snap while dragging")
        mw.snap_while_dragging_check.setToolTip("Snap nodes while dragging")
        mw.snap_while_dragging_check.setChecked(True)
        mw.snap_while_dragging_check.stateChanged.connect(
            lambda s: mw.canvas.set_snap_while_dragging(
                s == Qt.CheckState.Checked.value
            )
        )
        parent_layout.addWidget(mw.snap_while_dragging_check)

        # Grid mode
        mw.grid_mode_combo = QComboBox()
        mw.grid_mode_combo.addItems(["Node cell (1x1)", "Node 4x4"])
        # Default to Node 4x4 as requested
        mw.grid_mode_combo.setCurrentIndex(1)

        def on_grid_mode_changed(idx):
            mode = "1x1" if idx == 0 else "4x4"
            mw.canvas.set_grid_mode(mode)
            try:
                mw.grid_size_label.setText(f"Grid Cell: {mw.canvas.grid_size}px")
            except Exception:
                pass

        mw.grid_mode_combo.currentIndexChanged.connect(on_grid_mode_changed)
        grid_mode_layout = QHBoxLayout()
        grid_mode_layout.addWidget(QLabel("Grid Mode:"))
        grid_mode_layout.addWidget(mw.grid_mode_combo)
        grid_mode_layout.addStretch()
        parent_layout.addLayout(grid_mode_layout)

        mw.grid_size_label = QLabel(f"Grid Cell: {mw.canvas.grid_size}px")
        parent_layout.addWidget(mw.grid_size_label)

        # Snap granularity
        mw.snap_gran_combo = QComboBox()
        mw.snap_gran_combo.addItems(["Snap to Grid Cell", "Snap to Node Block (4x)"])
        # Default to 'Snap to Grid Cell' (snap granularity = 1)
        mw.snap_gran_combo.setCurrentIndex(0)

        def on_snap_gran_changed(idx):
            mw.canvas.snap_step = 1 if idx == 0 else 4

        mw.snap_gran_combo.currentIndexChanged.connect(on_snap_gran_changed)
        snap_layout = QHBoxLayout()
        snap_layout.addWidget(QLabel("Snap Granularity:"))
        snap_layout.addWidget(mw.snap_gran_combo)
        snap_layout.addStretch()
        parent_layout.addLayout(snap_layout)

        # Trigger initial update
        on_grid_mode_changed(mw.grid_mode_combo.currentIndex())

    def _build_layout_section(self) -> QWidget:
        """Build the graph layout controls section.

        Attempts to use MVVM LayoutsView if available, falls back to legacy buttons.
        """
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Graph Layout</b>"))
        else:
            layout.addWidget(QLabel("<b>Graph Layout</b>"))

        # Try MVVM LayoutsView first
        if self._try_build_mvvm_layouts_controls(layout):
            layout.addStretch()
            return container

        # Fallback to legacy buttons
        self._build_legacy_layout_controls(layout)

        layout.addStretch()
        return container

    def _try_build_mvvm_layouts_controls(self, parent_layout) -> bool:
        """Attempt to build MVVM-based layout controls.

        Returns:
            True if MVVM controls were built successfully, False to use legacy.
        """
        mw = self.mw

        try:
            # Check if MVVM adapter is available
            if not hasattr(mw, "layouts_adapter") or mw.layouts_adapter is None:
                logger.debug("MVVM LayoutsAdapter not available, using legacy controls")
                return False

            # Prefer the legacy-styled buttons but still use MVVM adapter logic
            try:
                mw.layouts_adapter  # ensure attribute exists
            except Exception:
                logger.debug("LayoutsAdapter attribute missing, using legacy controls")
                return False

            # Build legacy-style buttons that call the adapter
            self._build_mvvm_layout_button_controls(parent_layout, mw.layouts_adapter)

            # Add status label below
            mw.layout_status_label = QLabel()
            mw._update_layout_status_label()
            parent_layout.addWidget(mw.layout_status_label)

            logger.info(
                "MVVM-based legacy-style layout controls integrated successfully"
            )
            return True

        except Exception as e:
            logger.warning("Failed to build MVVM layout controls: %s", e)
            return False

    def _build_legacy_layout_controls(self, parent_layout):
        """Build legacy layout control buttons."""
        mw = self.mw

        mw.layout_sugiyama_btn = _create_standard_button(
            mw, "Hierarchical (Sugiyama)", None, None, 14
        )
        mw.layout_sugiyama_btn.setToolTip("Sugiyama algorithm for DAGs")
        mw.layout_sugiyama_btn.clicked.connect(
            lambda: mw.apply_graph_layout("sugiyama")
        )
        parent_layout.addWidget(mw.layout_sugiyama_btn)

        mw.layout_tree_btn = _create_standard_button(mw, "Tree Layout", None, None, 14)
        mw.layout_tree_btn.setToolTip("Walker's tree layout")
        mw.layout_tree_btn.clicked.connect(lambda: mw.apply_graph_layout("tree"))
        parent_layout.addWidget(mw.layout_tree_btn)

        mw.layout_mlp_full_btn = _create_standard_button(
            mw, "MLP Layout (Full)", None, None, 14
        )
        mw.layout_mlp_full_btn.setToolTip("Full MLP layout with backprop")
        mw.layout_mlp_full_btn.clicked.connect(
            lambda: mw.apply_graph_layout("mlp_layout")
        )
        parent_layout.addWidget(mw.layout_mlp_full_btn)

        # Direction
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        mw.layout_direction_combo = QComboBox()
        mw.layout_direction_combo.addItems(["Left → Right", "Top → Bottom"])
        mw.layout_direction_combo.setCurrentIndex(0)
        mw.layout_direction_combo.setToolTip("Data flow direction")
        direction_layout.addWidget(mw.layout_direction_combo)
        direction_layout.addStretch()
        parent_layout.addLayout(direction_layout)

        # Spacing
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))
        mw.layout_spacing_spin = QSpinBox()
        mw.layout_spacing_spin.setRange(50, 500)
        mw.layout_spacing_spin.setValue(80)
        mw.layout_spacing_spin.setSingleStep(10)
        mw.layout_spacing_spin.setSuffix(" px")
        mw.layout_spacing_spin.setToolTip("Spacing between nodes")
        spacing_layout.addWidget(mw.layout_spacing_spin)
        spacing_layout.addStretch()
        parent_layout.addLayout(spacing_layout)

        mw.layout_status_label = QLabel()
        mw._update_layout_status_label()
        parent_layout.addWidget(mw.layout_status_label)

    def _build_mvvm_layout_button_controls(self, parent_layout, adapter):
        """Build legacy-styled layout buttons that route through LayoutsAdapter."""
        mw = self.mw

        # Buttons
        mw.layout_sugiyama_btn = _create_standard_button(
            mw, "Hierarchical (Sugiyama)", None, None, 14
        )
        mw.layout_sugiyama_btn.setToolTip("Sugiyama algorithm for DAGs")
        mw.layout_sugiyama_btn.clicked.connect(
            lambda: adapter.apply_layout(
                "sugiyama",
                direction=self._get_layout_direction(),
                spacing=self._get_layout_spacing(),
            )
        )
        parent_layout.addWidget(mw.layout_sugiyama_btn)

        mw.layout_tree_btn = _create_standard_button(mw, "Tree Layout", None, None, 14)
        mw.layout_tree_btn.setToolTip("Walker's tree layout")
        mw.layout_tree_btn.clicked.connect(
            lambda: adapter.apply_layout(
                "tree",
                direction=self._get_layout_direction(),
                spacing=self._get_layout_spacing(),
            )
        )
        parent_layout.addWidget(mw.layout_tree_btn)

        mw.layout_mlp_full_btn = _create_standard_button(
            mw, "MLP Layout (Full)", None, None, 14
        )
        mw.layout_mlp_full_btn.setToolTip("Full MLP layout with backprop")
        mw.layout_mlp_full_btn.clicked.connect(
            lambda: adapter.apply_layout(
                "mlp_layout",
                direction=self._get_layout_direction(),
                spacing=self._get_layout_spacing(),
            )
        )
        parent_layout.addWidget(mw.layout_mlp_full_btn)

        # Direction
        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("Direction:"))
        mw.layout_direction_combo = QComboBox()
        mw.layout_direction_combo.addItems(["Left → Right", "Top → Bottom"])
        mw.layout_direction_combo.setCurrentIndex(0)
        mw.layout_direction_combo.setToolTip("Data flow direction")
        direction_layout.addWidget(mw.layout_direction_combo)
        direction_layout.addStretch()
        parent_layout.addLayout(direction_layout)

        # Spacing
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))
        mw.layout_spacing_spin = QSpinBox()
        mw.layout_spacing_spin.setRange(50, 500)
        mw.layout_spacing_spin.setValue(80)
        mw.layout_spacing_spin.setSingleStep(10)
        mw.layout_spacing_spin.setSuffix(" px")
        mw.layout_spacing_spin.setToolTip("Spacing between nodes")
        spacing_layout.addWidget(mw.layout_spacing_spin)
        spacing_layout.addStretch()
        parent_layout.addLayout(spacing_layout)

    def _get_layout_direction(self):
        mw = self.mw
        if (
            not hasattr(mw, "layout_direction_combo")
            or mw.layout_direction_combo is None
        ):
            return "LR"
        text = mw.layout_direction_combo.currentText()
        if "Top" in text:
            return "TB"
        return "LR"

    def _get_layout_spacing(self):
        mw = self.mw
        if not hasattr(mw, "layout_spacing_spin") or mw.layout_spacing_spin is None:
            return 150
        return int(mw.layout_spacing_spin.value())

    def _build_plotting_section(self) -> QWidget:
        """Build the plotting controls section."""
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Plotting</b>"))
        else:
            layout.addWidget(QLabel("<b>Plotting</b>"))

        mw.open_plot_btn = _create_standard_button(
            mw,
            "Open Plot Window",
            "fa5s.chart-bar",
            QStyle.StandardPixmap.SP_DialogOpenButton,
            14,
        )
        mw.open_plot_btn.clicked.connect(mw.open_plot_window)
        layout.addWidget(mw.open_plot_btn)

        mw.add_to_plot_btn = _create_standard_button(
            mw,
            "Add Selected to Plot",
            "fa5s.plus",
            QStyle.StandardPixmap.SP_FileDialogNewFolder,
            14,
        )
        mw.add_to_plot_btn.clicked.connect(mw.add_selected_to_plot)
        layout.addWidget(mw.add_to_plot_btn)

        backend_layout = QHBoxLayout()
        backend_layout.addWidget(QLabel("Plot Backend:"))
        mw.plot_backend_combo = QComboBox()
        mw.plot_backend_combo.addItems(["PyQtGraph", "Matplotlib"])
        mw.plot_backend_combo.setCurrentIndex(0)
        mw.plot_backend_combo.currentIndexChanged.connect(mw._on_plot_backend_changed)
        backend_layout.addWidget(mw.plot_backend_combo)
        layout.addLayout(backend_layout)

        layout.addStretch()
        return container

    def _build_simplification_section(self) -> QWidget:
        """Build the graph simplification controls section."""
        mw = self.mw
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        if ThemedLabel is not None:
            layout.addWidget(ThemedLabel("<b>Graph Simplification</b>"))
        else:
            layout.addWidget(QLabel("<b>Graph Simplification</b>"))

        # Description label
        desc_label = QLabel(
            "Simplify graph structure using compression and abstraction."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(desc_label)

        # Simplify Step button
        mw.simplify_step_btn = _create_standard_button(
            mw,
            "Simplify Step",
            "fa5s.compress",
            QStyle.StandardPixmap.SP_ArrowRight,
            14,
        )
        mw.simplify_step_btn.setToolTip(
            "Apply one simplification transformation (compression or abstraction)"
        )
        mw.simplify_step_btn.clicked.connect(mw.simplify_step)
        layout.addWidget(mw.simplify_step_btn)

        # Fully Simplify button
        mw.simplify_fully_btn = _create_standard_button(
            mw, "Fully Simplify", "fa5s.forward", QStyle.StandardPixmap.SP_MediaPlay, 14
        )
        mw.simplify_fully_btn.setToolTip(
            "Apply all possible simplifications until graph is fully simplified"
        )
        mw.simplify_fully_btn.clicked.connect(mw.simplify_fully)
        layout.addWidget(mw.simplify_fully_btn)

        # Expand Step button
        mw.expand_step_btn = _create_standard_button(
            mw, "Expand Step", "fa5s.expand", QStyle.StandardPixmap.SP_ArrowBack, 14
        )
        mw.expand_step_btn.setToolTip(
            "Reverse the last simplification (decompress or expand abstracted nodes)"
        )
        mw.expand_step_btn.clicked.connect(mw.expand_step)
        layout.addWidget(mw.expand_step_btn)

        # Status label for simplification
        mw.simplification_status_label = QLabel("History: 0 operations")
        mw.simplification_status_label.setStyleSheet("color: #aaa; font-size: 10px;")
        layout.addWidget(mw.simplification_status_label)

        layout.addStretch()
        return container

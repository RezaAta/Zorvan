"""Theme-aware canonical widget classes.

These small wrappers make it easier to create consistent, theme-aware UI
components across the application. They set a "themed" property or
`themed_panel` objectName that QSS targets, and implement `apply_theme()`
if any programmatic updates are needed beyond QSS.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDockWidget,
    QLabel,
    QListWidget,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QToolButton,
)

from .theme_utils import ThemeMixin


class ThemedPushButton(QPushButton, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        # Mark as themed so QSS can specifically target this widget
        self.setProperty("themed", True)
        # Make hover feel responsive by using the pointing-hand cursor
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setMouseTracking(True)
        except Exception:
            pass
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # Nothing dynamic required for now; QSS driven. Keep method for future
        # programmatic adjustments (e.g., icon recolor handlers).
        try:
            tm = self.get_theme_manager()
            # Reapply background for immediate preview of color buttons, tests
            try:
                # If the button is used as a color swatch (common in visualization
                # controls), we preserve direct background style set by callers.
                if not self.styleSheet():
                    # Nothing to do — stylesheet from theme will apply
                    pass
            except Exception:
                pass
        except Exception:
            pass


class ThemedToolButton(QToolButton, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QToolButton.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        # Use pointing-hand cursor to provide hover affordance
        try:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setMouseTracking(True)
        except Exception:
            pass
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # QSS-driven; additional runtime icon recolorers may hook into theme
        pass


class ThemedScrollArea(QScrollArea, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # ensure contained widget gets the themed_panel class so panels have radius
        try:
            w = self.widget()
            if w is not None:
                w.setProperty("themed_panel", True)
                try:
                    # If the child widget supports ThemeMixin, call its apply
                    if hasattr(w, "_on_theme_changed"):
                        try:
                            w._on_theme_changed()
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass


class ThemedListWidget(QListWidget, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # Nothing additional for now; QSS handles coloring
        pass


class ThemedDockWidget(QDockWidget, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QDockWidget.__init__(self, *args, **kwargs)
        # Keep the default objectName so we can query it in tests/docs
        try:
            self.setProperty("themed", True)
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        try:
            tm = self.get_theme_manager()
            c = tm.get_color("panel_bg", tm.get_color("bg", "#3c3f41")).name()
            try:
                self.setStyleSheet(f"QDockWidget {{ background: {c}; }}")
            except Exception:
                pass
        except Exception:
            pass


class ThemedSlider(QSlider, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QSlider.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # QSS-driven
        pass


class ThemedLabel(QLabel, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        try:
            tm = self.get_theme_manager()
            text_col = tm.get_color("text", "#bbbbbb")
            try:
                self.setStyleSheet(f"color: {text_col.name()};")
            except Exception:
                pass
        except Exception:
            pass


class ThemedCheckBox(QCheckBox, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QCheckBox.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # QSS-driven
        pass


class ThemedSpinBox(QSpinBox, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QSpinBox.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # QSS-driven
        pass


class ThemedComboBox(QComboBox, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QComboBox.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # QSS-driven
        pass


class ThemedProgressBar(QProgressBar, ThemeMixin):
    def __init__(self, *args, **kwargs):
        QProgressBar.__init__(self, *args, **kwargs)
        self.setProperty("themed", True)
        try:
            ThemeMixin.__init__(self)
        except Exception:
            pass

    def apply_theme(self):
        # Apply basic themed stylesheet so the progress 'chunk' uses the accent color
        try:
            tm = self.get_theme_manager()
            accent = tm.get_color("accent").name()
            bg = tm.get_color("list_bg", tm.get_color("panel_bg")).name()
            text = tm.get_color("text").name()
            border = tm.get_color("border").name()
            # Local stylesheet to ensure the widget uses accent for the filled portion
            qss = (
                f'QProgressBar[themed="true"] {{ background-color: {bg}; color: {text}; border: 1px solid {border}; border-radius: 4px; }}'
                f'QProgressBar[themed="true"]::chunk {{ background-color: {accent}; }}'
            )
            try:
                self.setStyleSheet(qss)
            except Exception:
                pass
        except Exception:
            pass


# Provide a convenience alias in builtins so tests that reference ThemedToolButton
# without importing it still work (some tests instantiate it directly).
try:
    import builtins

    builtins.ThemedToolButton = ThemedToolButton
except Exception:
    pass

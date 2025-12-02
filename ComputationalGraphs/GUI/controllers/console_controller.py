"""
ConsoleController - Manages the in-app console panel and output redirection.

Extracted from MainWindow as part of Clean Code refactoring.
Handles console panel creation, stdout/stderr redirection, and console output.
"""
import sys
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QTextEdit
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..main_window import MainWindow


class ConsoleController:
    """Controller for in-app console panel and output management."""

    def __init__(self, main_window: 'MainWindow'):
        self.main_window = main_window
        self._orig_stdout = None
        self._orig_stderr = None

    def create_console_panel(self):
        """Create a docked console for verbose/debug output."""
        mw = self.main_window
        
        dock = QDockWidget("Console", mw)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea | 
            Qt.DockWidgetArea.RightDockWidgetArea
        )

        container = QWidget()
        v = QVBoxLayout(container)
        v.setContentsMargins(4, 4, 4, 4)

        # Console text area (read-only)
        mw.console_text = QTextEdit()
        mw.console_text.setReadOnly(True)
        # Dark theme to match app
        mw.console_text.setStyleSheet(
            "background-color: #1e1e1e; color: #e6e6e6; "
            "font-family: Segoe UI; font-size: 11px;"
        )
        v.addWidget(mw.console_text)

        # Connect the signal so writes are thread-safe
        try:
            mw.console_write.connect(mw.console_text.append)
        except Exception:
            pass

        # Controls: clear and echo-to-terminal
        btn_layout = QHBoxLayout()
        mw.clear_console_btn = QPushButton("Clear")
        mw.clear_console_btn.clicked.connect(lambda: mw.console_text.clear())
        btn_layout.addWidget(mw.clear_console_btn)

        mw.echo_terminal_check = QCheckBox("Echo to terminal")
        mw.echo_terminal_check.setChecked(True)
        btn_layout.addWidget(mw.echo_terminal_check)

        btn_layout.addStretch()
        v.addLayout(btn_layout)

        dock.setWidget(container)
        mw.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        try:
            dock.hide()
        except Exception:
            pass
        mw.console_dock = dock

        # Set up stdout/stderr redirection
        self._setup_output_redirection()

    def _setup_output_redirection(self):
        """Redirect stdout/stderr to the in-app console."""
        mw = self.main_window

        class ConsoleRedirector:
            def __init__(self, main_win, orig_stream, name='stdout'):
                self.main_win = main_win
                self.orig = orig_stream
                self.name = name

            def write(self, msg):
                if not msg:
                    return
                try:
                    # Emit signal to append safely in the GUI thread
                    try:
                        self.main_win.console_write.emit(msg)
                    except Exception:
                        # Fallback to directly appending if signal not connected
                        try:
                            self.main_win.console_text.append(msg)
                        except Exception:
                            pass
                finally:
                    try:
                        # Always forward to the original stream
                        self.orig.write(msg)
                    except Exception:
                        pass

            def flush(self):
                try:
                    self.orig.flush()
                except Exception:
                    pass

        try:
            # Keep originals to restore later if needed
            self._orig_stdout = sys.stdout
            self._orig_stderr = sys.stderr
            # Also store on main_window for write_to_console access
            mw._orig_stdout = self._orig_stdout
            mw._orig_stderr = self._orig_stderr
            sys.stdout = ConsoleRedirector(mw, self._orig_stdout, 'stdout')
            sys.stderr = ConsoleRedirector(mw, self._orig_stderr, 'stderr')
        except Exception:
            # If redirect fails, ignore silently
            pass

    def write_to_console(self, message: str, verbose_only: bool = False):
        """Append a message to the in-app console.

        Args:
            message: The message to write
            verbose_only: If True, only write when verbose mode is enabled
        """
        mw = self.main_window
        
        try:
            if verbose_only and not getattr(mw, 'verbose_check', None):
                # If verbose UI control hasn't been created yet, fall back to printing
                print(message)
                return

            if verbose_only and not mw.verbose_check.isChecked():
                return

            # Append message with newline and auto-scroll
            mw.console_text.append(message)
            mw.console_text.moveCursor(mw.console_text.textCursor().End)

            # Echo to terminal if requested
            if (getattr(mw, 'echo_terminal_check', None) and 
                mw.echo_terminal_check.isChecked()):
                try:
                    # Use original stdout to avoid recursive redirection
                    if self._orig_stdout:
                        self._orig_stdout.write(message + "\n")
                    elif hasattr(mw, '_orig_stdout'):
                        mw._orig_stdout.write(message + "\n")
                    else:
                        print(message)
                except Exception:
                    try:
                        print(message)
                    except Exception:
                        pass
        except Exception:
            # Fallback: print to terminal
            print(message)

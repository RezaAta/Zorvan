"""MVVM wrapper view for the Combined Node Palette.

This small wrapper uses the existing `CombinedNodePalette` implementation and
binds a `CombinedNodePaletteViewModel` to it. It provides a migration path and
keeps the heavy legacy widget intact while enabling testable VM behavior.
"""

from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from ..viewmodels.combined_node_palette_viewmodel import CombinedNodePaletteViewModel


class CombinedNodePaletteView(QWidget):
    def __init__(self, vm: CombinedNodePaletteViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm
        # Lazy initialization of the legacy palette widget so we can bind
        try:
            from zorvan.GUI.combined_node_palette import CombinedNodePalette

            self._palette = CombinedNodePalette(parent)
        except Exception:
            # Fall back to an empty QWidget for headless tests
            self._palette = QWidget(parent)

        # Create wrapper main widget so we can add a persistent create button
        self._main_widget = QWidget(parent)
        main_layout = QVBoxLayout(self._main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar - place for optional controls (create button exists here when
        # underlying palette does not provide one).
        top_bar = QWidget(self._main_widget)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(2, 2, 2, 2)
        top_layout.addStretch()

        # Fallback create button (shown only when underlying palette lacks a create control)
        self._create_btn = QPushButton("Create Custom Node", top_bar)
        try:
            self._create_btn.setProperty("themed", True)
            self._create_btn.setCursor(self._create_btn.cursor())
            # Keep some modest sizing so it matches other buttons visually
            self._create_btn.setMinimumWidth(110)
            self._create_btn.setMaximumWidth(220)
        except Exception:
            pass
        # Wire to VM
        try:
            self._create_btn.clicked.connect(self.vm.trigger_create)
        except Exception:
            pass

        # Only add the fallback button to the top bar for now - we will hide it
        # if the underlying palette already exposes a create button so there
        # aren't duplicate controls.
        top_layout.addWidget(self._create_btn)
        main_layout.addWidget(top_bar)

        # Add the underlying palette widget below the top bar
        main_layout.addWidget(self._palette)

        # Bind search bar changes to VM (prefer underlying search if present)
        try:
            if hasattr(self._palette, "search_bar"):
                self._palette.search_bar.textChanged.connect(self.vm.set_search_text)
        except Exception:
            pass

        # Wire underlying create button to VM and hide fallback if possible
        try:
            if hasattr(self._palette, "create_btn"):
                self._palette.create_btn.clicked.connect(self.vm.trigger_create)
                # Underlying palette supplies a create control - hide the fallback
                try:
                    self._create_btn.setVisible(False)
                except Exception:
                    pass
            # Support the older NodePalette naming too
            elif hasattr(self._palette, "create_custom_button"):
                self._palette.create_custom_button.clicked.connect(
                    self.vm.trigger_create
                )
                try:
                    self._create_btn.setVisible(False)
                except Exception:
                    pass
        except Exception:
            pass

        # When VM fires select events, the adapter will allow handlers to be set
        # (We still rely on the legacy widget to deliver mouse drag or click events)

    def widget(self):
        return self._main_widget

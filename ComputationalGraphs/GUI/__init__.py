"""GUI module for ComputationalGraphs visual editor.

This package avoids importing PyQt6-backed submodules at import time so the
non-GUI parts of the package can be imported during CI/test runs that do not
have PyQt6 installed. Tests and code that explicitly import GUI submodules
can still do so (they import the submodule directly), but importing
`ComputationalGraphs.GUI` will not attempt to import PyQt6 unless it's
available.
"""

__all__ = ["examples_loader"]

try:
    # If PyQt6 is available, it's safe to import GUI top-level classes.
    import PyQt6  # type: ignore

    # Import GUI components only if GUI backend available
    from .backprop_dialog import BackpropDialog  # type: ignore
    from .examples_loader import ExamplesLoader  # type: ignore
    from .main_window import MainWindow  # type: ignore
    from .mlp_dialog import MLPGeneratorDialog  # type: ignore

    __all__ = ["MainWindow", "ExamplesLoader", "MLPGeneratorDialog", "BackpropDialog"]
except Exception:
    # PyQt6 not present - avoid importing GUI submodules and keep package lightweight.
    pass

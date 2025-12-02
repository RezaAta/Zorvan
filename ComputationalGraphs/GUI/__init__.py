"""
GUI module for ComputationalGraphs visual editor.
"""

from .backprop_dialog import BackpropDialog
from .examples_loader import ExamplesLoader
from .main_window import MainWindow
from .mlp_dialog import MLPGeneratorDialog

__all__ = ["MainWindow", "ExamplesLoader", "MLPGeneratorDialog", "BackpropDialog"]

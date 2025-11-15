"""
GUI module for ComputationalGraphs visual editor.
"""

from .main_window import MainWindow
from .examples_loader import ExamplesLoader
from .mlp_dialog import MLPGeneratorDialog
from .backprop_dialog import BackpropDialog

__all__ = [
    'MainWindow',
    'ExamplesLoader',
    'MLPGeneratorDialog',
    'BackpropDialog'
]

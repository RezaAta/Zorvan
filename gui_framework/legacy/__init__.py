"""
Transitional compatibility helpers for gui_framework.

This package entrypoint centralizes runtime access to the legacy GUI API so
other gui_framework modules can import from a single compatibility layer
while migration is in progress.
"""

from typing import TYPE_CHECKING, Any, Dict

try:
    from .controllers.file_io_controller import FileIOController
except Exception:  # pragma: no cover
    FileIOController = None

try:
    from .controllers.graph_layout_controller import GraphLayoutController
except Exception:  # pragma: no cover
    GraphLayoutController = None

try:
    from .controllers.dialog_controller import DialogController
except Exception:  # pragma: no cover
    DialogController = None

try:
    from .graph_runner import GraphRunner
except Exception:  # pragma: no cover
    GraphRunner = None

try:
    from .combined_node_palette import CombinedNodePalette, NodeItemWidget
except Exception:  # pragma: no cover
    CombinedNodePalette = None
    NodeItemWidget = None

try:
    from .custom_node_dialog import CustomNodeDialog
except Exception:  # pragma: no cover
    CustomNodeDialog = None

try:
    from .custom_node_manager import CustomNodeDefinition, CustomNodeManager, get_custom_node_manager
except Exception:  # pragma: no cover
    CustomNodeDefinition = None
    CustomNodeManager = None
    get_custom_node_manager = None

try:
    from . import custom_node_manager
except Exception:  # pragma: no cover
    custom_node_manager = None

try:
    from . import custom_node_dialog
except Exception:  # pragma: no cover
    custom_node_dialog = None

try:
    from . import custom_node_dialog_adapter
except Exception:  # pragma: no cover
    custom_node_dialog_adapter = None

try:
    from .controllers import control_panel_builder
except Exception:  # pragma: no cover
    control_panel_builder = None

try:
    from .controllers.control_panel_builder import _apply_icon, _create_standard_button
except Exception:  # pragma: no cover
    _apply_icon = None
    _create_standard_button = None

try:
    from .node_registry import get_node_categories
except Exception:  # pragma: no cover
    get_node_categories = None

try:
    from .theme_widgets import ThemedScrollArea, ThemedLabel, ThemedPushButton, ThemedProgressBar
except Exception:  # pragma: no cover
    ThemedScrollArea = None
    ThemedLabel = None
    ThemedPushButton = None
    ThemedProgressBar = None

try:
    from .graph_canvas import SubgraphControlButton
except Exception:  # pragma: no cover
    SubgraphControlButton = None

try:
    from .replace_node_dialog import ReplaceNodeDialog
except Exception:  # pragma: no cover
    ReplaceNodeDialog = None

try:
    from .inspector_pane import InspectorPane
except Exception:  # pragma: no cover
    InspectorPane = None

try:
    from .node_short_names import get_short_name
except Exception:  # pragma: no cover
    get_short_name = None

try:
    from .commands import (
        AddEdgeCommand,
        AddNodeCommand,
        MoveNodesCommand,
        RemoveItemsCommand,
        ReplaceNodeCommand,
        SwallowNodeCommand,
    )
except Exception:  # pragma: no cover
    AddEdgeCommand = None
    AddNodeCommand = None
    MoveNodesCommand = None
    RemoveItemsCommand = None
    ReplaceNodeCommand = None
    SwallowNodeCommand = None

try:
    from .learning_rate_dialog import LearningRateDialog
except Exception:  # pragma: no cover
    LearningRateDialog = None

try:
    from .custom_node_dialog_adapter import CustomNodeDialogAdapter
except Exception:  # pragma: no cover
    CustomNodeDialogAdapter = None

try:
    from .combined_node_palette_adapter import CombinedNodePaletteAdapter
except Exception:  # pragma: no cover
    CombinedNodePaletteAdapter = None

try:
    from .plot_window import PlotWindow, create_plot_window
except Exception:  # pragma: no cover
    PlotWindow = None
    create_plot_window = None

try:
    from .plot_view import PlotView
except Exception:  # pragma: no cover
    PlotView = None

try:
    from .graph_canvas import GraphCanvas
except Exception:  # pragma: no cover
    GraphCanvas = None

try:
    from .node_editor_dialog import NodeEditorDialog
except Exception:  # pragma: no cover
    NodeEditorDialog = None

try:
    from .mlp_dialog import MLPGeneratorDialog
except Exception:  # pragma: no cover
    MLPGeneratorDialog = None

try:
    from .node_item import NodeItem
except Exception:  # pragma: no cover
    NodeItem = None

try:
    from .layouts import MLPLayoutEngine
except Exception:  # pragma: no cover
    MLPLayoutEngine = None

try:
    from .color_preferences import ColorPreferencesDialog
except Exception:  # pragma: no cover
    ColorPreferencesDialog = None

try:
    from .predecessors_dialog import PredecessorsDialog
except Exception:  # pragma: no cover
    PredecessorsDialog = None

try:
    from .controllers.graph_builder_controller import GraphBuilderController
except Exception:  # pragma: no cover
    GraphBuilderController = None

try:
    from .controllers.control_panel_builder import _IconHoverFilter
except Exception:  # pragma: no cover
    _IconHoverFilter = None

try:
    from .node_factory import create_node, is_registered
except Exception:  # pragma: no cover
    create_node = None
    is_registered = None

try:
    from .controllers.execution_controller import ExecutionController
except Exception:  # pragma: no cover
    ExecutionController = None

try:
    from .backprop_dialog import BackpropDialog
except Exception:  # pragma: no cover
    BackpropDialog = None

try:
    from .activation_dialog import ActivationDialog
except Exception:  # pragma: no cover
    ActivationDialog = None

try:
    from .main_window import MainWindow as LegacyMainWindow, CollapsibleSection
except Exception:  # pragma: no cover
    LegacyMainWindow = None
    CollapsibleSection = None

MainWindow = LegacyMainWindow

try:
    from . import layouts as legacy_layouts
except Exception:  # pragma: no cover
    legacy_layouts = None

layouts = legacy_layouts

try:
    from .examples_loader import ExamplesLoader
except Exception:  # pragma: no cover
    ExamplesLoader = None

try:
    from . import theme
except Exception:  # pragma: no cover
    theme = None

theme_module = theme

try:
    from .theme import get_theme_manager, ThemeManager, _is_test_env
except Exception:  # pragma: no cover
    get_theme_manager = None
    ThemeManager = None
    _is_test_env = False

if TYPE_CHECKING:
    from .controllers.file_io_controller import FileIOController as _FileIOController
    from .controllers.graph_layout_controller import GraphLayoutController as _GraphLayoutController
    from .controllers.dialog_controller import DialogController as _DialogController
    from .graph_runner import GraphRunner as _GraphRunner
    from .combined_node_palette import CombinedNodePalette as _CombinedNodePalette
    from .combined_node_palette import NodeItemWidget as _NodeItemWidget
    from .combined_node_palette_adapter import CombinedNodePaletteAdapter as _CombinedNodePaletteAdapter
    from .custom_node_dialog import CustomNodeDialog as _CustomNodeDialog
    from .custom_node_manager import CustomNodeDefinition as _CustomNodeDefinition
    from .custom_node_manager import CustomNodeManager as _CustomNodeManager
    from .controllers import control_panel_builder as _control_panel_builder
    from .controllers.control_panel_builder import _apply_icon as __apply_icon, _create_standard_button as __create_standard_button
    from .main_window import MainWindow as _LegacyMainWindow, CollapsibleSection as _CollapsibleSection
    from .examples_loader import ExamplesLoader as _ExamplesLoader
    from .theme import ThemeManager as _ThemeManager
    from .theme_widgets import ThemedScrollArea as _ThemedScrollArea, ThemedLabel as _ThemedLabel, ThemedPushButton as _ThemedPushButton
    from .graph_canvas import SubgraphControlButton as _SubgraphControlButton
    from .replace_node_dialog import ReplaceNodeDialog as _ReplaceNodeDialog
    from .inspector_pane import InspectorPane as _InspectorPane
    from .node_short_names import get_short_name as _get_short_name
    from .commands import SwallowNodeCommand as _SwallowNodeCommand
    from .learning_rate_dialog import LearningRateDialog as _LearningRateDialog
    from .custom_node_dialog_adapter import CustomNodeDialogAdapter as _CustomNodeDialogAdapter
    from .combined_node_palette_adapter import CombinedNodePaletteAdapter as _CombinedNodePaletteAdapter
    from .controllers import control_panel_builder as _control_panel_builder
    from .controllers.control_panel_builder import _apply_icon as __apply_icon, _create_standard_button as __create_standard_button
    from .plot_window import PlotWindow as _PlotWindow
    from .plot_view import PlotView as _PlotView
    from .graph_canvas import GraphCanvas as _GraphCanvas
    from .node_editor_dialog import NodeEditorDialog as _NodeEditorDialog
    from .mlp_dialog import MLPGeneratorDialog as _MLPGeneratorDialog
    from .node_item import NodeItem as _NodeItem
    from .layouts import MLPLayoutEngine as _MLPLayoutEngine
    from .color_preferences import ColorPreferencesDialog as _ColorPreferencesDialog
    from .predecessors_dialog import PredecessorsDialog as _PredecessorsDialog
    from .controllers.graph_builder_controller import GraphBuilderController as _GraphBuilderController
    from .controllers.control_panel_builder import _IconHoverFilter as __IconHoverFilter
    from .node_factory import create_node as _create_node, is_registered as _is_registered
    from .controllers.execution_controller import ExecutionController as _ExecutionController
    from .backprop_dialog import BackpropDialog as _BackpropDialog
    from .activation_dialog import ActivationDialog as _ActivationDialog


def get_node_categories_safe() -> Dict[str, Dict]:
    if callable(get_node_categories):
        try:
            return get_node_categories()
        except Exception:
            pass
    return {}


def get_custom_node_manager_safe():
    if callable(get_custom_node_manager):
        try:
            return get_custom_node_manager()
        except Exception:
            pass
    return None

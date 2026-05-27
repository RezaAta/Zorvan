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
    from .custom_node_manager import (
        CustomNodeDefinition,
        CustomNodeManager,
        get_custom_node_manager,
    )
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
    from .controllers.control_panel_builder import _ICON_REAPPLY_HANDLERS
except Exception:  # pragma: no cover
    _ICON_REAPPLY_HANDLERS = None

try:
    from .node_registry import get_node_categories
except Exception:  # pragma: no cover
    get_node_categories = None

try:
    from .theme_widgets import (
        ThemedCheckBox,
        ThemedComboBox,
        ThemedLabel,
        ThemedProgressBar,
        ThemedPushButton,
        ThemedScrollArea,
        ThemedSlider,
        ThemedSpinBox,
    )
except Exception:  # pragma: no cover
    ThemedCheckBox = None
    ThemedComboBox = None
    ThemedScrollArea = None
    ThemedLabel = None
    ThemedPushButton = None
    ThemedProgressBar = None
    ThemedSlider = None
    ThemedSpinBox = None

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
    import importlib

    _cp = importlib.import_module(".color_preferences", __package__)
    _cp_cls = getattr(_cp, "ColorPreferencesDialog", None)
    if _cp_cls is not None:
        ColorPreferencesDialog = _cp_cls
except Exception:  # pragma: no cover
    pass

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
    from .main_window import CollapsibleSection
    from .main_window import MainWindow as LegacyMainWindow
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
    from .theme import ThemeManager, _is_test_env, get_theme_manager
except Exception:  # pragma: no cover
    get_theme_manager = None
    ThemeManager = None
    _is_test_env = False

if TYPE_CHECKING:
    from .activation_dialog import ActivationDialog as _ActivationDialog
    from .backprop_dialog import BackpropDialog as _BackpropDialog
    from .color_preferences import ColorPreferencesDialog as _ColorPreferencesDialog
    from .combined_node_palette import CombinedNodePalette as _CombinedNodePalette
    from .combined_node_palette import NodeItemWidget as _NodeItemWidget
    from .combined_node_palette_adapter import (
        CombinedNodePaletteAdapter as _CombinedNodePaletteAdapter,
    )
    from .commands import SwallowNodeCommand as _SwallowNodeCommand
    from .controllers import control_panel_builder as _control_panel_builder
    from .controllers.control_panel_builder import _apply_icon as __apply_icon
    from .controllers.control_panel_builder import (
        _create_standard_button as __create_standard_button,
    )
    from .controllers.control_panel_builder import _IconHoverFilter as __IconHoverFilter
    from .controllers.dialog_controller import DialogController as _DialogController
    from .controllers.execution_controller import (
        ExecutionController as _ExecutionController,
    )
    from .controllers.file_io_controller import FileIOController as _FileIOController
    from .controllers.graph_builder_controller import (
        GraphBuilderController as _GraphBuilderController,
    )
    from .controllers.graph_layout_controller import (
        GraphLayoutController as _GraphLayoutController,
    )
    from .custom_node_dialog import CustomNodeDialog as _CustomNodeDialog
    from .custom_node_dialog_adapter import (
        CustomNodeDialogAdapter as _CustomNodeDialogAdapter,
    )
    from .custom_node_manager import CustomNodeDefinition as _CustomNodeDefinition
    from .custom_node_manager import CustomNodeManager as _CustomNodeManager
    from .examples_loader import ExamplesLoader as _ExamplesLoader
    from .graph_canvas import GraphCanvas as _GraphCanvas
    from .graph_canvas import SubgraphControlButton as _SubgraphControlButton
    from .graph_runner import GraphRunner as _GraphRunner
    from .inspector_pane import InspectorPane as _InspectorPane
    from .layouts import MLPLayoutEngine as _MLPLayoutEngine
    from .learning_rate_dialog import LearningRateDialog as _LearningRateDialog
    from .main_window import CollapsibleSection as _CollapsibleSection
    from .main_window import MainWindow as _LegacyMainWindow
    from .mlp_dialog import MLPGeneratorDialog as _MLPGeneratorDialog
    from .node_editor_dialog import NodeEditorDialog as _NodeEditorDialog
    from .node_factory import create_node as _create_node
    from .node_factory import is_registered as _is_registered
    from .node_item import NodeItem as _NodeItem
    from .node_short_names import get_short_name as _get_short_name
    from .plot_view import PlotView as _PlotView
    from .plot_window import PlotWindow as _PlotWindow
    from .predecessors_dialog import PredecessorsDialog as _PredecessorsDialog
    from .replace_node_dialog import ReplaceNodeDialog as _ReplaceNodeDialog
    from .theme import ThemeManager as _ThemeManager
    from .theme_widgets import ThemedLabel as _ThemedLabel
    from .theme_widgets import ThemedPushButton as _ThemedPushButton
    from .theme_widgets import ThemedScrollArea as _ThemedScrollArea


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


def __getattr__(name: str):
    if name == "ColorPreferencesDialog":
        try:
            import importlib

            _cp = importlib.import_module(".color_preferences", __package__)
            _cp_cls = getattr(_cp, "ColorPreferencesDialog", None)
            if _cp_cls is not None:
                globals()[name] = _cp_cls
                return _cp_cls
        except Exception:
            pass
    raise AttributeError(f"module {__name__} has no attribute {name}")

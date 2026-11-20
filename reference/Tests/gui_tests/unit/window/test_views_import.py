import pytest

import gui_framework.views.examples_loader_view as examples_loader_view
import gui_framework.views.inspector_view as inspector_view
import gui_framework.views.node_editor_dialog as node_editor_dialog


def test_inspector_view_import_behaviour():
    if not inspector_view.HAS_PYQT:
        with pytest.raises(ImportError):
            inspector_view.InspectorView()
    else:
        # In environments with PyQt, instantiation should succeed
        w = inspector_view.InspectorView  # No-op: class exists
        assert w is not None


def test_node_editor_dialog_import_behaviour():
    if not node_editor_dialog.HAS_PYQT:
        with pytest.raises(ImportError):
            node_editor_dialog.NodeEditorDialog()
    else:
        w = node_editor_dialog.NodeEditorDialog
        assert w is not None


def test_examples_loader_view_import_behaviour():
    if not examples_loader_view.HAS_PYQT:
        with pytest.raises(ImportError):
            examples_loader_view.ExamplesLoaderView()
    else:
        w = examples_loader_view.ExamplesLoaderView
        assert w is not None

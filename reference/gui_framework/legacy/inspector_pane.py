"""
Thin adapter to expose the MVVM InspectorView as a legacy GUI component.
"""

try:
    from gui_framework.viewmodels.inspector_viewmodel import InspectorViewModel
    from gui_framework.views.inspector_view import InspectorView
except Exception as e:
    raise ImportError("Inspector MVVM components are not available: " + str(e))


class InspectorPane:
    """Adapter that wraps the InspectorView for use by legacy code.

    Usage:
        pane = InspectorPane(canvas_vm, parent)
        pane.show()
    """

    def __init__(self, canvas_vm=None, parent=None):
        # Accept either an existing InspectorViewModel or a CanvasViewModel
        if isinstance(canvas_vm, InspectorViewModel):
            self._vm = canvas_vm
        else:
            self._vm = InspectorViewModel(canvas_vm)
            try:
                self._vm.initialize()
            except Exception:
                pass
        self._view = InspectorView(self._vm, parent)

    def widget(self):
        return self._view

    def show(self):
        try:
            self._view.show()
        except Exception:
            pass

    def close(self):
        try:
            self._view.close()
        except Exception:
            pass

    def get_viewmodel(self):
        return self._vm

    def __getattr__(self, name):
        # Delegate unknown attributes to the underlying view
        return getattr(self._view, name)

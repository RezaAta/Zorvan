import types

from gui_framework.adapters.layouts_adapter import LayoutsAdapter


class DummyCombo:
    def __init__(self):
        self._index = 0

    def setCurrentIndex(self, idx):
        self._index = idx

    def currentIndex(self):
        return self._index


class DummySpin:
    def __init__(self, value=150):
        self._value = value

    def setValue(self, v):
        self._value = int(v)

    def value(self):
        return self._value


class DummyLayoutController:
    def __init__(self):
        self.called = False
        self.args = None

    def apply_graph_layout(self, layout_type, spacing=None):
        self.called = True
        self.args = (layout_type, spacing)


def test_apply_layout_routes_to_controller_and_sets_ui():
    mw = types.SimpleNamespace()
    mw.layout_direction_combo = DummyCombo()
    mw.layout_spacing_spin = DummySpin()

    dummy_ctrl = DummyLayoutController()
    mw.graph_layout_controller = dummy_ctrl

    adapter = LayoutsAdapter(mw)

    # Apply with TB direction and custom spacing
    adapter.apply_layout("sugiyama", direction="TB", spacing=200)

    assert dummy_ctrl.called is True
    assert dummy_ctrl.args == ("sugiyama", 200)
    assert mw.layout_direction_combo.currentIndex() == 1
    assert mw.layout_spacing_spin.value() == 200

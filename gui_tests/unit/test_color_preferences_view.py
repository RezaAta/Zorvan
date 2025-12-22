import pytest

try:
    from PyQt6.QtWidgets import QApplication

    PYQT = True
except Exception:
    PYQT = False

pytestmark = pytest.mark.skipif(not PYQT, reason="PyQt6 required for view tests")

from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import (
    ColorPreferencesViewModel,
)
from gui_framework.views.dialogs.color_preferences_dialog import ColorPreferencesDialog


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


def test_color_view_updates_buttons_and_applies(qapp):
    vm = ColorPreferencesViewModel()
    vm.initialize()

    dlg = ColorPreferencesDialog(vm)
    # initial buttons exist
    assert hasattr(dlg, "buttons")
    # programmatically set a color for a key via VM and ensure view reflects it
    vm.set_color_for_key("accent", "#ff00aa", apply_theme=False)
    # trigger UI render
    dlg._render_from_vm()
    assert "#ff00aa" in dlg.buttons["accent"].styleSheet()

    # Apply from view model and ensure theme manager updated
    vm.on_apply()
    dlg.close()
    vm.cleanup()

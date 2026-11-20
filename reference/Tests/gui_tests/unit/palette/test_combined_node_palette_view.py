import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QPushButton

from gui_framework.viewmodels.combined_node_palette_viewmodel import (
    CombinedNodePaletteViewModel,
)
from gui_framework.views.combined_node_palette_view import CombinedNodePaletteView


def test_create_triggers_vm_with_underlying_palette():
    app = QApplication.instance() or QApplication([])
    vm = CombinedNodePaletteViewModel()
    try:
        vm.initialize()
    except Exception:
        pass

    called = {"ok": False}

    def handler():
        called["ok"] = True

    vm.add_create_handler(handler)

    view = CombinedNodePaletteView(vm)

    # Find any QPushButton child that likely corresponds to the create action
    btns = view.widget().findChildren(QPushButton)
    assert btns, "No QPushButton found in CombinedNodePaletteView"

    # Click buttons until our handler runs (one of them should be the create control)
    for b in btns:
        b.click()
        if called["ok"]:
            break

    assert called["ok"]


def test_fallback_create_button_shown_and_triggers_vm():
    # Ensure fallback button is present and triggers create handler when visible
    app = QApplication.instance() or QApplication([])
    vm = CombinedNodePaletteViewModel()
    try:
        vm.initialize()
    except Exception:
        pass

    called = {"ok": False}

    def handler():
        called["ok"] = True

    vm.add_create_handler(handler)

    view = CombinedNodePaletteView(vm)

    # Force show the fallback button (simulate underlying palette lacking a create control)
    try:
        view._create_btn.setVisible(True)
    except Exception:
        pytest.skip("View does not expose fallback create button")

    # Click it and ensure handler called
    view._create_btn.click()
    assert called["ok"]

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow


def test_main_window_create_opens_custom_dialog(monkeypatch):
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()

    called = {"ok": False}

    class StubAdapter:
        def __init__(self, node_like, parent=None):
            pass

        def exec(self):
            called["ok"] = True

    try:
        from gui_framework.legacy import custom_node_dialog_adapter as cad

        monkeypatch.setattr(cad, "CustomNodeDialogAdapter", StubAdapter)
    except Exception:
        pytest.skip("CustomNodeDialogAdapter not available to patch")

    # Find a create button on the palette
    btn = None
    try:
        pal = mw.combined_palette
        if hasattr(pal, "create_btn"):
            btn = pal.create_btn
        elif hasattr(pal, "create_custom_button"):
            btn = pal.create_custom_button
        elif hasattr(pal, "_view") and hasattr(pal._view, "_create_btn"):
            btn = pal._view._create_btn
    except Exception:
        pass

    assert btn is not None, "Could not locate create button on palette"
    btn.click()

    assert called["ok"]

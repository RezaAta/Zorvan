from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import SubgraphControlButton


def test_subgraph_control_button_initializes_with_fa_or_text():
    # Ensure a QApplication exists (tests may run headless but creating an app is safe)
    app = QApplication.instance() or QApplication([])

    # Create with a FontAwesome-like identifier; should not raise and should either
    # produce a pixmap item (if qtawesome available) or fall back to a text item.
    btn = SubgraphControlButton("fa5s.trash", lambda: None)
    assert hasattr(btn, "callback") and callable(btn.callback)
    assert (
        getattr(btn, "_pixmap_item", None) is not None
        or getattr(btn, "_text_item", None) is not None
    )


def test_subgraph_control_button_text_icon():
    # Plain text icon should create a text item
    btn2 = SubgraphControlButton("All", lambda: None)
    assert getattr(btn2, "_text_item", None) is not None

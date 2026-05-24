import pytest

# Skip GUI tests when PyQt6 isn't available in CI environments
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import MainWindow


def test_toolbar_has_add_selected_to_plot_button():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    assert hasattr(
        mw, "toolbar_add_to_plot_btn"
    ), "Toolbar should have an 'add to plot' button"
    btn = mw.toolbar_add_to_plot_btn
    assert btn.text() == "add to plot"
    assert btn.toolTip() == "Add currently selected nodes to the plot window"
    # cleanup
    try:
        mw.close()
    except Exception:
        pass


def test_toolbar_does_not_have_rebuild_btn():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()
    # Rebuild button should not be in top toolbar; it's accessible in the control panel only
    assert not hasattr(
        mw, "rebuild_btn"
    ), "Top toolbar should not include a 'rebuild' button"
    try:
        mw.close()
    except Exception:
        pass

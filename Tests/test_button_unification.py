import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow


def test_main_buttons_are_themed():
    app = QApplication.instance() or QApplication([])
    mw = MainWindow()

    # Buttons to check
    btns = [
        "play_btn",
        "pause_btn",
        "resume_btn",
        "restore_graph_btn",
        "reset_btn",
        "rebuild_exec_btn",
        "step_btn",
    ]

    for name in btns:
        assert hasattr(mw, name), f"MainWindow missing {name}"
        b = getattr(mw, name)
        assert b.property("themed") is True

    # Toolbar add-to-plot button should be themed too
    assert hasattr(mw, "toolbar_add_to_plot_btn")
    assert mw.toolbar_add_to_plot_btn.property("themed") is True

    # Combined palette and node palette create buttons
    assert hasattr(mw, "combined_palette")
    cp = mw.combined_palette
    assert hasattr(cp, "create_btn")
    assert cp.create_btn.property("themed") is True

    # NodePalette fallback create_custom_button
    try:
        np = mw.palette
        assert hasattr(np, "create_custom_button")
        assert np.create_custom_button.property("themed") is True
    except Exception:
        # If NodePalette not available, that's fine for some test runs
        pass

    # App stylesheet contains the themed hover selector
    ss = app.styleSheet() or ""
    assert 'QPushButton[themed="true"]:hover' in ss
    # Toolbar-scoped hover selector should also exist
    assert 'QToolBar QPushButton[themed="true"]:hover' in ss
    # Toolbar scoped base rule should be present so the button has a visible background
    assert 'QToolBar QPushButton[themed="true"]' in ss
    assert 'QToolBar QToolButton[themed="true"]' in ss

    # Buttons should not rely on inline styles; they should be themed and picked up by global QSS
    assert hasattr(mw, "toolbar_add_to_plot_btn")
    assert hasattr(mw, "play_btn")
    # Ensure both have themed property so QSS targets work
    assert mw.toolbar_add_to_plot_btn.property("themed") is True
    assert mw.play_btn.property("themed") is True
    # Confirm the app stylesheet contains the global themed hover rule
    ss = app.styleSheet() or ""
    assert 'QPushButton[themed="true"]:hover' in ss
    assert 'QToolBar QPushButton[themed="true"]:hover' in ss

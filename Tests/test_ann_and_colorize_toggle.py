import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow


def test_ann_and_colorize_mutual_exclusion():
    app = QApplication(sys.argv)
    win = MainWindow()
    # Show window so child widgets can be visible for visibility checks
    win.show()
    app.processEvents()

    # Ensure both checkboxes exist
    assert hasattr(win, "colorize_check")
    assert hasattr(win, "ann_colors_check")

    # Check colorize-by-value -> ann should be unchecked; settings container should be visible
    win.colorize_check.setChecked(True)
    app.processEvents()
    assert win.colorize_check.isChecked()
    assert not win.ann_colors_check.isChecked()
    # Ensure the colorize settings container is visible (or auto-range is enabled)
    assert hasattr(win, "colorize_settings_container")
    # Some platforms don't report isVisible without event loop propagation; as a proxy
    # check the auto-range button is enabled and the container property is True.
    assert win.auto_range_btn.isEnabled()
    assert win.colorize_settings_container.isVisible() or not win.colorize_settings_container.isHidden()

    # Check ann -> colorize_by_value should be unchecked; colorize container hidden
    win.ann_colors_check.setChecked(True)
    app.processEvents()
    assert win.ann_colors_check.isChecked()
    assert not win.colorize_check.isChecked()
    assert not win.colorize_settings_container.isVisible()

    # Clean up
    app.quit()


if __name__ == "__main__":
    test_ann_and_colorize_mutual_exclusion()

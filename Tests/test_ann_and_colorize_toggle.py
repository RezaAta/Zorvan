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
    assert (
        win.colorize_settings_container.isVisible()
        or not win.colorize_settings_container.isHidden()
    )

    # Check ann -> colorize_by_value should be unchecked; colorize container hidden
    win.ann_colors_check.setChecked(True)
    app.processEvents()
    assert win.ann_colors_check.isChecked()
    assert not win.colorize_check.isChecked()
    assert not win.colorize_settings_container.isVisible()

    # Clear should be present inside the colorize group container and appear as the last control
    assert hasattr(win, "colorize_group_container")
    # Find clear button in the colorize group layout children
    cg_layout = win.colorize_group_layout
    last_item = cg_layout.itemAt(cg_layout.count() - 1)
    assert last_item is not None
    # Last item should be a layout row containing the clear button
    from PyQt6.QtWidgets import QPushButton

    last_widget = None
    if last_item.layout():
        # inspect children of the row layout for a QPushButton named Clear
        row_layout = last_item.layout()
        for i in range(row_layout.count()):
            w = row_layout.itemAt(i).widget()
            if isinstance(w, QPushButton) and w.text() == "Clear":
                last_widget = w
                break
    assert last_widget is not None

    # Clean up
    app.quit()


if __name__ == "__main__":
    test_ann_and_colorize_mutual_exclusion()

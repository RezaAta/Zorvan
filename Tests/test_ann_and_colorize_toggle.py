import sys

from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.main_window import MainWindow


def test_ann_and_colorize_mutual_exclusion():
    app = QApplication(sys.argv)
    win = MainWindow()

    # Ensure both checkboxes exist
    assert hasattr(win, "colorize_check")
    assert hasattr(win, "ann_colors_check")

    # Check colorize-by-value -> ann should be unchecked
    win.colorize_check.setChecked(True)
    assert win.colorize_check.isChecked()
    assert not win.ann_colors_check.isChecked()

    # Check ann -> colorize_by_value should be unchecked
    win.ann_colors_check.setChecked(True)
    assert win.ann_colors_check.isChecked()
    assert not win.colorize_check.isChecked()

    # Clean up
    app.quit()


if __name__ == "__main__":
    test_ann_and_colorize_mutual_exclusion()

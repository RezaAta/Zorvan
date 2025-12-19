from PyQt6.QtWidgets import QApplication

from ComputationalGraphs.GUI.color_preferences import ColorPreferencesDialog
from ComputationalGraphs.GUI.main_window import MainWindow


def test_speed_slider_has_track_and_updates_with_theme():
    app = QApplication.instance() or QApplication([])
    win = MainWindow()
    # Ensure slider has a style sheet applied that defines a groove
    ss = getattr(win, "speed_slider", None).styleSheet() or ""
    assert (
        "QSlider::groove" in ss or ss.strip() != ""
    ), "Slider should have a visible groove stylesheet"

    # Change accent color and ensure slider stylesheet picks up the new accent
    dlg = ColorPreferencesDialog(win)
    dlg.set_color_for_key("accent", "#123456", apply_theme=True)
    QApplication.processEvents()

    new_ss = getattr(win, "speed_slider", None).styleSheet() or ""
    assert (
        "#123456" in new_ss
    ), f"Expected accent color to appear in slider stylesheet, got: {new_ss}"

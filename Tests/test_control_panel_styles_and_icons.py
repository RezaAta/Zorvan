from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import CollapsibleSection, MainWindow


def test_control_panel_styles_and_processing_queue_icon():
    # Ensure QApplication exists
    if QApplication.instance() is None:
        _app = QApplication([])

    win = MainWindow()
    dock = win.control_dock
    scroll = dock.widget()
    panel = scroll.widget()

    # Style sanity: styles should not concatenate selectors without spaces
    ss = panel.styleSheet()
    assert ";Q" not in ss, f"Found concatenated selector in stylesheet: {ss}"

    # Find the 'Processing Queue' collapsible section and ensure it has an icon
    found = None
    for section in panel.findChildren(CollapsibleSection):
        if section.toggle_button.text().strip().startswith("Processing Queue"):
            found = section
            break
    assert found is not None, "Processing Queue section not found"
    icon = found.toggle_button.icon()
    # Icon should be set (either font-awesome or QStyle fallback)
    assert not icon.isNull(), "Processing Queue header icon is not set"

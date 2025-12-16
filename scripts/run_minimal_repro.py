import traceback

from PyQt6.QtWidgets import QApplication, QPushButton

try:
    print("Constructing QApplication")
    app = QApplication([])
    print("Importing filter")
    from ComputationalGraphs.GUI.controllers.control_panel_builder import (
        _IconHoverFilter,
    )

    print("Imported filter OK")
    btn = QPushButton()
    print("Created QPushButton OK")
except Exception:
    traceback.print_exc()
    raise

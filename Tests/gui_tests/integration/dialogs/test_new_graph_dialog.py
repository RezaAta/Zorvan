import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow

try:
    from gui_framework.views.dialogs.new_graph_dialog import NewGraphDialog

    PYQT = True
except Exception:
    PYQT = False


@pytest.mark.skipif(not PYQT, reason="PyQt6 not available")
def test_new_graph_dialog_from_menu(qapp):
    mw = MainWindow()
    mw.show()

    # Schedule dialog interaction after action triggers
    def interact_with_dialog():
        # Find the dialog and perform interactions
        for w in QApplication.topLevelWidgets():
            if isinstance(w, NewGraphDialog):
                # Set fields
                try:
                    w.name_edit.setText("IntegrationGraph")
                except Exception:
                    pass
                try:
                    w.inputs_spin.setValue(5)
                    w.outputs_spin.setValue(2)
                    w.type_combo.setCurrentIndex(1)  # ANFIS
                except Exception:
                    pass

                # Accept the dialog
                try:
                    w._on_accept()
                except Exception:
                    try:
                        w.accept()
                    except Exception:
                        pass
                return

    # Trigger creation via the menu action (Tools -> Create New Graph...)
    QTimer.singleShot(50, lambda: mw.create_graph_action.trigger())
    QTimer.singleShot(150, interact_with_dialog)

    # Run loop briefly to allow dialog to show and be handled
    QTimer.singleShot(300, QApplication.instance().quit)
    QApplication.instance().exec()

    # After dialog accepted, main window graph should be replaced
    assert getattr(mw, "graph", None) is not None
    assert getattr(mw.graph, "name", None) == "IntegrationGraph"

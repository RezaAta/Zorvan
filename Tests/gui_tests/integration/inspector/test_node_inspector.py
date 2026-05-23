import pytest
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from zorvan.GUI.main_window import MainWindow
from zorvan.Nodes.Node import Node

try:
    from gui_framework.views.dialogs.node_properties_dialog import NodePropertiesDialog

    PYQT = True
except Exception:
    PYQT = False


@pytest.mark.skipif(not PYQT, reason="PyQt6 not available")
def test_inspect_node_from_menu(qapp):
    mw = MainWindow()
    mw.show()

    # Create a simple graph with one node and visualize
    g = mw.graph
    n = Node(name="InspectMe")
    # minimal node fields used by visualization
    try:
        g.nodes.append(n)
    except Exception:
        pass
    try:
        mw._visualize_graph_on_canvas(g)
    except Exception:
        pass

    # Select the node item in the canvas
    def select_node_item():
        for it in mw.canvas.scene.items():
            try:
                if (
                    getattr(it, "node", None)
                    and getattr(it.node, "name", None) == "InspectMe"
                ):
                    it.setSelected(True)
                    break
            except Exception:
                pass

    QTimer.singleShot(20, select_node_item)

    # Interact with dialog after menu action triggers
    def interact_with_dialog():
        for w in QApplication.topLevelWidgets():
            if isinstance(w, NodePropertiesDialog):
                try:
                    w.name_edit.setText("Inspected")
                except Exception:
                    pass
                try:
                    w.color_edit.setText("#112233")
                except Exception:
                    pass
                try:
                    w._on_accept()
                except Exception:
                    try:
                        w.accept()
                    except Exception:
                        pass
                return

    QTimer.singleShot(50, lambda: mw.inspect_node_action.trigger())
    QTimer.singleShot(150, interact_with_dialog)
    QTimer.singleShot(300, QApplication.instance().quit)
    QApplication.instance().exec()

    # Verify graph node was updated
    names = [getattr(nod, "name", None) for nod in mw.graph.nodes]
    assert "Inspected" in names

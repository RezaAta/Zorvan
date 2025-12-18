from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication, QWidget

from ComputationalGraphs.GUI.combined_node_palette import CombinedNodePalette


def test_create_delegates_to_parent_palette():
    app = QApplication.instance() or QApplication([])

    class Dummy:
        called = False

        def on_create_custom_node(self):
            Dummy.called = True

    parent = QWidget()
    parent.palette = Dummy()

    palette = CombinedNodePalette(parent)
    # call on_create and ensure parent's palette method was called
    palette.on_create()
    assert Dummy.called is True


def test_keyboard_navigation_moves_focus():
    app = QApplication.instance() or QApplication([])

    class DummyPalette:
        node_categories = {
            "Cat": {
                "description": "desc",
                "nodes": [
                    ("A", "One", "x"),
                    ("B", "Two", "x"),
                    ("C", "Three", "x"),
                ],
            }
        }

    parent = QWidget()
    parent.palette = DummyPalette()
    palette = CombinedNodePalette(parent)

    # Ensure there are 3 widgets
    visible = [w for w, c, _ in palette._node_widgets if not w.isHidden()]
    assert len(visible) == 3

    # Show palette so widgets can accept focus
    parent.show()
    palette.show()
    palette.activateWindow()
    QApplication.processEvents()

    # Focus the first widget and ensure it has focus
    visible[0].setFocus(Qt.FocusReason.MouseFocusReason)
    QApplication.processEvents()
    assert QApplication.focusWidget() == visible[0]

    # Send Key_Down
    event = QKeyEvent(
        QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier
    )
    palette.keyPressEvent(event)
    QApplication.processEvents()

    # Focus should have moved to second widget
    assert QApplication.focusWidget() == visible[1]

"""Quick smoke test: instantiate NodeEditorDialog for InitializableContainerNode and call reinit handler."""

import sys

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import NodeEditorDialog
from zorvan.Nodes.InitializableContainerNode import InitializableContainerNode


def main():
    app = QApplication(sys.argv)

    node = InitializableContainerNode(
        name="W_test", value=0.0, init_low=-1.0, init_high=1.0
    )
    dlg = NodeEditorDialog(node)

    # Emulate the user pressing the reinitialize button: call the handler directly
    dlg.on_reinitialize_weight()
    print("Reinitialized value:", node.value)


if __name__ == "__main__":
    main()

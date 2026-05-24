import sys

import pytest

# Skip GUI tests when PyQt6 isn't available in the environment
pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from gui_framework.legacy import NodeItem
from zorvan.Nodes.BufferNode import BufferNode
from zorvan.Nodes.SigmoidNode import SigmoidNode


def run_test():
    created_app = False
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    # Create a buffer node and a sigmoid node
    buf = BufferNode(name="Buff_T", size=3)
    sig = SigmoidNode(name="Sig_T")
    # Simulate buffer have values
    buf.buffer = [None, 0.5, 1.0]
    buf.value = 0.5
    # Node items
    buf_item = NodeItem(buf)
    sig_item = NodeItem(sig)
    try:
        buf_item.update_value_display()
        sig_item.update_value_display()
        print(
            "NodeItem update_value_display executed without exception for buffer and normal nodes."
        )
    except Exception as e:
        print("ERROR: update_value_display raised exception:", type(e), e)

    # Quit application if we created it
    if created_app:
        app.quit()


if __name__ == "__main__":
    run_test()

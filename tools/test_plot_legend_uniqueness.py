# Quick test for PlotWindow legend uniqueness
import sys

from PyQt6.QtWidgets import QApplication

# Ensure the package imports work - we run from repo root
from zorvan.GUI.plot_window import PlotWindow
from zorvan.Nodes.DataStreamNode import DataStreamNode


def print_labels(pw):
    # Try to get labels from pw.lines values
    try:
        labels = [ln.get_label() for ln in pw.lines.values()]
    except Exception:
        labels = []
    print(labels)


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    # Create three nodes with the same name
    n1 = DataStreamNode("same")
    n2 = DataStreamNode("same")
    n3 = DataStreamNode("same")

    print("\nCreating PlotWindow with three nodes having the same name:")
    pw = PlotWindow([n1, n2, n3], max_iterations=100)

    # Print labels after initial creation
    print("Initial labels:")
    print_labels(pw)

    # Add another node with the same name via add_node
    n4 = DataStreamNode("same")
    print("\nAdding another node with the same name via add_node:")
    pw.add_node(n4)
    print("Labels after add_node:")
    print_labels(pw)

    # Remove a node - set the combo to the second node and remove
    # Find index of n2 in current nodes
    if n2 in pw.nodes:
        idx = pw.nodes.index(n2)
        pw.node_combo.setCurrentIndex(idx)
        print(f"\nRemoving node at index {idx} (name={n2.name}):")
        pw.remove_selected_node()
        print("Labels after remove_selected_node:")
        print_labels(pw)
    else:
        print("Node to remove not found in pw.nodes")

    # Clean up and exit
    pw.close()
    app.quit()


if __name__ == "__main__":
    main()

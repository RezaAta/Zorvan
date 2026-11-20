"""
Test script for Canvas Interaction (Phase 4 Stage 2).

Tests node dragging, selection, and keyboard shortcuts without requiring a display.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Test that CanvasViewModel selection methods work
from gui_framework.viewmodels.canvas_viewmodel import (
    CanvasViewModel,
    EdgeRenderState,
    NodeRenderState,
)


def test_selection_logic():
    """Test ViewModel selection logic."""
    print("Testing CanvasViewModel selection logic...")

    # Create ViewModel
    vm = CanvasViewModel()

    # Add some nodes
    nodes = [
        NodeRenderState(node_id="A", name="A", x=0, y=0),
        NodeRenderState(node_id="B", name="B", x=100, y=0),
        NodeRenderState(node_id="C", name="C", x=0, y=100),
    ]

    vm._nodes = {n.node_id: n for n in nodes}
    vm.nodes_changed += 1

    # Test single selection
    vm.select_node("A")
    assert vm.is_node_selected("A"), "Node A should be selected"
    assert not vm.is_node_selected("B"), "Node B should not be selected"
    assert len(vm.get_selected_nodes()) == 1, "Should have 1 selected node"
    print("✓ Single selection works")

    # Test multi-selection
    vm.select_node("B", add_to_selection=True)
    assert vm.is_node_selected("A"), "Node A should still be selected"
    assert vm.is_node_selected("B"), "Node B should be selected"
    assert len(vm.get_selected_nodes()) == 2, "Should have 2 selected nodes"
    print("✓ Multi-selection works")

    # Test deselection
    vm.deselect_node("A")
    assert not vm.is_node_selected("A"), "Node A should be deselected"
    assert vm.is_node_selected("B"), "Node B should still be selected"
    print("✓ Deselection works")

    # Test clear selection
    vm.clear_selection()
    assert len(vm.get_selected_nodes()) == 0, "Should have no selected nodes"
    print("✓ Clear selection works")

    # Test select all
    vm.select_all_nodes()
    assert len(vm.get_selected_nodes()) == 3, "Should have all 3 nodes selected"
    print("✓ Select all works")

    print("✅ All ViewModel selection tests passed!\n")


def test_node_movement():
    """Test node position updates."""
    print("Testing node position updates...")

    vm = CanvasViewModel()

    # Add a node
    node = NodeRenderState(node_id="A", name="A", x=0, y=0)
    vm._nodes = {"A": node}

    # Update position
    vm.update_node_position("A", 100, 200)
    assert vm._nodes["A"].x == 100, "X position should be updated"
    assert vm._nodes["A"].y == 200, "Y position should be updated"
    print("✓ Single node position update works")

    # Add more nodes
    vm._nodes["B"] = NodeRenderState(node_id="B", name="B", x=0, y=0)
    vm._nodes["C"] = NodeRenderState(node_id="C", name="C", x=0, y=0)

    # Update multiple positions
    vm.update_node_positions(
        {
            "A": (50, 50),
            "B": (100, 100),
            "C": (150, 150),
        }
    )
    assert vm._nodes["A"].x == 50 and vm._nodes["A"].y == 50
    assert vm._nodes["B"].x == 100 and vm._nodes["B"].y == 100
    assert vm._nodes["C"].x == 150 and vm._nodes["C"].y == 150
    print("✓ Multiple node position update works")

    print("✅ All node movement tests passed!\n")


def test_commands():
    """Test undo/redo commands."""
    print("Testing undo/redo commands...")

    from gui_framework.commands import MoveNodesCommand

    vm = CanvasViewModel()
    vm._nodes = {
        "A": NodeRenderState(node_id="A", name="A", x=0, y=0),
        "B": NodeRenderState(node_id="B", name="B", x=100, y=100),
    }

    # Create move command
    positions = {
        "A": (0, 0, 50, 50),
        "B": (100, 100, 150, 150),
    }
    command = MoveNodesCommand(vm, positions)

    # Execute (redo)
    command.redo()
    assert vm._nodes["A"].x == 50 and vm._nodes["A"].y == 50
    assert vm._nodes["B"].x == 150 and vm._nodes["B"].y == 150
    print("✓ Command redo works")

    # Undo
    command.undo()
    assert vm._nodes["A"].x == 0 and vm._nodes["A"].y == 0
    assert vm._nodes["B"].x == 100 and vm._nodes["B"].y == 100
    print("✓ Command undo works")

    # Test command merging
    command2 = MoveNodesCommand(
        vm,
        {
            "A": (50, 50, 100, 100),
            "B": (150, 150, 200, 200),
        },
    )

    merged = command.mergeWith(command2)
    assert merged, "Commands should merge"
    assert command.positions["A"] == (
        0,
        0,
        100,
        100,
    ), "Merged command should have original start and final end"
    print("✓ Command merging works")

    print("✅ All command tests passed!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Canvas Interaction Tests (Phase 4 Stage 2)")
    print("=" * 60)
    print()

    try:
        test_selection_logic()
        test_node_movement()
        test_commands()

        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nPhase 4 Stage 2 (Canvas Interaction) is functional!")
        print("\nFeatures verified:")
        print("  • Node selection (single and multi)")
        print("  • Node deselection and clear selection")
        print("  • Select all nodes")
        print("  • Node position updates (single and batch)")
        print("  • Undo/redo commands for moves")
        print("  • Command merging for efficient undo")
        print("\nNote: This test verifies ViewModel logic.")
        print("Visual interaction requires PyQt6 and display libraries.")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

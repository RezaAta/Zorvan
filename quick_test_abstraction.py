#!/usr/bin/env python3
"""
Quick test of AbstractNode functionality without pytest.
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode


def test_basic_abstraction():
    """Test basic AbstractNode creation."""
    print("Testing basic abstraction...")
    graph = Graph()

    # Create input node
    input_node = DataStreamNode("input", [1, 2, 3])
    graph.AddNode(input_node)

    # Create two disjoint addition nodes
    add_a = AdditionNode("add_a")
    add_b = AdditionNode("add_b")
    graph.AddNode(add_a)
    graph.AddNode(add_b)

    # Both have the same predecessor
    add_a.AddPreNode(input_node)
    add_b.AddPreNode(input_node)

    # Create output node
    output = AdditionNode("output")
    graph.AddNode(output)

    # Both have the same successor
    output.AddPreNode(add_a)
    output.AddPreNode(add_b)

    # Check abstraction is valid
    can_abstract, reason = graph.can_abstract_nodes([add_a, add_b])
    print(f"  Can abstract: {can_abstract} - {reason}")
    assert can_abstract, f"Should be able to abstract: {reason}"

    # Perform abstraction
    abstract = graph.AbstractNodes([add_a, add_b])
    print(f"  Abstract node created: {abstract.name} (type: {type(abstract).__name__})")
    assert abstract is not None
    assert abstract.name.startswith("A"), "Abstract node should be named A#"
    assert len(abstract) == 2, "Should contain 2 nodes"

    # Check graph structure
    assert (
        len(graph.nodes) == 3
    ), f"Graph should have 3 nodes (input, abstract, output), got {len(graph.nodes)}"
    assert abstract in graph.nodes
    assert add_a not in graph.nodes
    assert add_b not in graph.nodes

    # Check connections
    assert (
        input_node in abstract.predecessors
    ), "Input should be predecessor of abstract"
    assert abstract in output.predecessors, "Abstract should be predecessor of output"

    print("  ✓ Basic abstraction test passed!")
    return True


def test_abstract_expand():
    """Test abstracting and then expanding."""
    print("\nTesting abstraction + expansion...")
    graph = Graph()

    # Create input
    input_node = DataStreamNode("input", [1])
    graph.AddNode(input_node)

    # Create two disjoint nodes
    add_a = AdditionNode("add_a")
    add_b = AdditionNode("add_b")
    add_a.AddPreNode(input_node)
    add_b.AddPreNode(input_node)
    graph.AddNode(add_a)
    graph.AddNode(add_b)

    # Create output
    output = AdditionNode("output")
    output.AddPreNode(add_a)
    output.AddPreNode(add_b)
    graph.AddNode(output)

    # Abstract
    abstract = graph.AbstractNodes([add_a, add_b])
    print(f"  Created abstract node: {abstract.name}")
    assert len(graph.nodes) == 3

    # Expand
    restored = graph.ExpandAbstractNode(abstract)
    print(f"  Expanded abstract node, restored {len(restored)} nodes")
    assert len(restored) == 2
    assert add_a in restored
    assert add_b in restored
    assert len(graph.nodes) == 4  # input, add_a, add_b, output
    assert abstract not in graph.nodes

    print("  ✓ Abstraction + expansion test passed!")
    return True


def test_abstract_validation():
    """Test that invalid abstractions are rejected."""
    print("\nTesting abstraction validation...")
    graph = Graph()

    # Create a scenario where abstraction should fail
    input_node = DataStreamNode("input", [1])
    graph.AddNode(input_node)

    # Create two nodes with different predecessors
    add_a = AdditionNode("add_a")
    add_b = AdditionNode("add_b")

    source_a = AdditionNode("source_a")
    source_b = AdditionNode("source_b")

    graph.AddNode(add_a)
    graph.AddNode(add_b)
    graph.AddNode(source_a)
    graph.AddNode(source_b)

    add_a.AddPreNode(source_a)
    add_b.AddPreNode(source_b)  # Different predecessor!

    # This should fail abstraction
    can_abstract, reason = graph.can_abstract_nodes([add_a, add_b])
    print(f"  Abstraction allowed: {can_abstract} - Reason: {reason}")
    assert not can_abstract, "Should reject nodes with different predecessors"

    print("  ✓ Abstraction validation test passed!")
    return True


if __name__ == "__main__":
    try:
        test_basic_abstraction()
        test_abstract_expand()
        test_abstract_validation()
        print("\n" + "=" * 50)
        print("✓ All abstraction tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)

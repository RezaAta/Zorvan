import pytest

from ComputationalGraphs.Core.Graph import Graph

from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode


def test_transfer_node_attributes():
    g = Graph()
    c1 = ContainerNode(name='W1', value=3.14)
    c2 = ContainerNode(name='W2', value=0.0)
    g.AddNode(c1, c2)
    # Transfer attributes from c1 to c2
    g.TransferNodeAttributes(c1, c2)
    assert c2.value == pytest.approx(3.14)


def test_replicate_connections_incoming_outgoing():
    g = Graph()
    a = DataStreamNode(name='x0')
    b = AdditionNode(name='Add_1')
    c = MultiplicationNode(name='Mul_1')
    g.AddNode(a, b, c)
    g.ConnectPreNode(b, a)  # a -> b
    g.ConnectPreNode(c, b)  # b -> c
    # Replace b with a multiplication node (new node type)
    new_b = MultiplicationNode(name='Mul_new')
    g.ReplaceNode(new_b, b)

    # Verify connections: a should be predecessor of new_b, and c should be successor (new_b in c.predecessors)
    assert new_b in g.nodes
    assert a in new_b.predecessors
    assert any(pred is new_b for pred in c.predecessors)


def test_replace_starting_node_is_preserved_in_starting_nodes():
    g = Graph()
    ds = DataStreamNode(name='x0')
    add = AdditionNode(name='add')
    g.AddNode(ds, add)
    g.starting_nodes = [ds]
    # Replace ds with a DataStreamNode copy and ensure starting_nodes updated
    new_ds = DataStreamNode(name='x1', data=[9, 9])
    g.ReplaceNode(new_ds, ds)
    assert new_ds in g.nodes
    assert ds not in g.nodes
    assert len(g.starting_nodes) == 1
    assert g.starting_nodes[0] is new_ds

from zorvan.Nodes.SequencerNode import SequencerNode


def test_sequencer_node_preserves_input_order_for_list_of_lists():
    node = SequencerNode("Dynamic Buffer")

    assert node.Operation([1, 2]) == [1, 2]
    assert node.Operation([[3, 4], [5, 6]]) == [3, 4]
    assert node.Operation(None) == [5, 6]
    assert node.Operation(None) is None

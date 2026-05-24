from zorvan.Nodes.ListNode import ListNode


def test_list_node_accumulates_inputs_and_invalidates_with_none_when_disallowed():
    node = ListNode(name="list", allowNone=False)

    assert node.Operation(1) == [1]
    node.midCalculation = True
    assert node.Operation(2) == [1, 2]
    assert node.Operation(None) is None
    assert node.Operation(3) is None

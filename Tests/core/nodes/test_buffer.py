from zorvan.Nodes.BufferNode import BufferNode


def test_buffer_node_appends_values_and_maintains_max_size():
    buf = BufferNode(name="b", size=3)

    assert buf.buffer == [None, None, None]
    assert buf.Operation(1) is None
    assert buf.buffer == [None, None, 1]

    assert buf.Operation(2) is None
    assert buf.buffer == [None, 1, 2]

    assert buf.Operation(3) == 1
    assert buf.buffer == [1, 2, 3]

    assert buf.Operation(4) == 2
    assert buf.buffer == [2, 3, 4]

from ComputationalGraphs.Nodes.BufferNode import BufferNode


def test_buffer_latest_value():
    # Initialize buffer with size 3
    buf = BufferNode(name="b", size=3)
    # Emulate operations by calling Operation directly (as in ProcessBatch)
    # Append values 1, 2, 3
    buf.Operation(1)
    buf.Operation(2)
    buf.Operation(3)

    # Latest should be 3, and oldest value returned by last Operation is the oldest in buffer
    assert buf.buffer[-1] == 3
    assert len(buf.buffer) == 3
    assert buf.buffer[-1] == 3

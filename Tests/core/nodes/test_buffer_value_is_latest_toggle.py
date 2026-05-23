from zorvan.Nodes.BufferNode import BufferNode


def test_buffer_default_behavior():
    buf = BufferNode(name="buf", size=3)
    # buffer starts as [None, None, None]
    out1 = buf.Operation(1)  # append 1 => buffer becomes [None, None, 1]
    # value should be oldest, still None or first non-None
    assert out1 is None or out1 == None
    out2 = buf.Operation(2)  # append 2 => buffer becomes [None, 1, 2]
    assert out2 == None or out2 == None
    out3 = buf.Operation(3)  # append 3 => buffer becomes [1, 2, 3]
    assert out3 == 1


def test_buffer_latest_property():
    buf_latest = BufferNode(name="buf_latest", size=3)
    # Append items and ensure latest property reflects the most recent appended element
    buf_latest.Operation(1)  # buffer: [None, None, 1]
    assert buf_latest.buffer[-1] == 1
    buf_latest.Operation(2)  # buffer: [None, 1, 2]
    assert buf_latest.buffer[-1] == 2
    buf_latest.Operation(3)  # buffer: [1, 2, 3]
    assert buf_latest.buffer[-1] == 3

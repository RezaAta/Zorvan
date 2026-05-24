from zorvan.Nodes.DataStreamNode import DataStreamNode


def test_data_stream_node_advances_after_initial_delay():
    node = DataStreamNode("dataStream", [4, 2, 3], initialDelay=5)

    assert node.value == 4

    for _ in range(7):
        node.Operation()

    assert node.value == 3
    assert node.iteration == 7

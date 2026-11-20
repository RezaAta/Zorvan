def test_reference_package_uses_rearchitecture_name():
    from zorvan_reference.Core.Graph import Graph

    assert Graph.__name__ == "Graph"

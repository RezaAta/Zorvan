from gui_framework.viewmodels.mlp_generator_viewmodel import MLPGeneratorViewModel


def test_mlp_generator_creates_graph_structure():
    gen = MLPGeneratorViewModel()
    g = gen.generate(num_inputs=2, hidden_layers=[3, 2], num_outputs=1)

    assert hasattr(g, "nodes")
    names = [n.name for n in g.nodes]
    # expect input nodes x0,x1 and outputs y0
    assert "x0" in names and "x1" in names and "y0" in names
    # check hidden node naming
    assert any(n.startswith("H0N") for n in names)

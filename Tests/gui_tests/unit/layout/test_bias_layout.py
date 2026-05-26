from gui_framework.legacy import ExamplesLoader, MLPLayoutEngine


def test_bias_and_db_placement():
    loader = ExamplesLoader()
    g = loader._build_piecewise_mlp2_concurrent()
    engine = MLPLayoutEngine(g.nodes, grid_size=10)
    pos = engine.layout()

    # Iterate hidden add nodes layer by layer
    hidden_adds = [n for n in g.nodes if getattr(n, "name", "").startswith("Add_L")]
    hidden_adds.sort(key=lambda n: engine.get_last_number(n))
    # Group by layer id
    layers = {}
    for add in hidden_adds:
        import re

        m = re.match(r"Add_L(\d+)N(\d+)", add.name)
        if m:
            layer = int(m.group(1))
            layers.setdefault(layer, []).append(add)

    for layer_id, adds in layers.items():
        prev_bias_coords = None
        for idx, add in enumerate(
            sorted(adds, key=lambda n: engine.get_last_number(n))
        ):
            add_gx, add_gy = engine.get_grid_coords(add)
            # Find bias predecessors for this add
            bias_preds = [
                p
                for p in getattr(add, "predecessors", [])
                if getattr(p, "name", "").startswith("B_")
            ]
            if not bias_preds:
                continue
            bias = bias_preds[0]
            bias_gx, bias_gy = engine.get_grid_coords(bias)
            if idx == 0:
                # First bias should be above its add
                assert (
                    bias_gx == add_gx
                ), f"Bias gx {bias_gx} not equal to add gx {add_gx} for {bias.name}"
                assert (
                    bias_gy == add_gy + 1
                ), f"Bias gy {bias_gy} not above add gy {add_gy} for {bias.name}"
            else:
                # Subsequent bias should be (+1, +1) from previous bias
                assert prev_bias_coords is not None
                assert bias_gx == prev_bias_coords[0] + 1
                assert bias_gy == prev_bias_coords[1] + 1
            prev_bias_coords = (bias_gx, bias_gy)

    # Check dB nodes are placed above their bias nodes
    bias_nodes = [n for n in g.nodes if getattr(n, "name", "").startswith("B_")]
    for bias in bias_nodes:
        bias_gx, bias_gy = engine.get_grid_coords(bias)
        db_preds = [
            p
            for p in getattr(bias, "predecessors", [])
            if getattr(p, "name", "").startswith("dB_")
        ]
        for db in db_preds:
            db_gx, db_gy = engine.get_grid_coords(db)
            assert db_gx == bias_gx
            assert db_gy == bias_gy + 1

    # If reached here, placement asserts passed
    print("Bias and dB placement checks passed")

    # Check BiasOne placement relative to LR nodes after Backprop layout
    from zorvan.Core.BackpropGraph import BackpropGraph
    from zorvan.Core.Graph import Graph
    from zorvan.Core.MLPGraph import MLPGraph

    mlp = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1, use_bias=True)
    mlp.BuildMLP()
    backprop = BackpropGraph(mlp, learningRate=0.01)
    backprop.BuildBackprop()
    # Create a full graph and add mlp/backprop nodes
    full_graph = Graph()
    for n in mlp.nodes:
        full_graph.AddNode(n)
    for n in backprop.nodes:
        full_graph.AddNode(n)

    engine2 = MLPLayoutEngine(full_graph.nodes, grid_size=10)
    engine2.layout()

    # Find LR and BiasOne placements
    lr_nodes = [
        n
        for n in full_graph.nodes
        if getattr(n, "name", "") == "LearningRate"
        or getattr(n, "name", "").lower() == "lr"
    ]
    biasone_nodes = [n for n in full_graph.nodes if getattr(n, "name", "") == "BiasOne"]
    assert lr_nodes, "LearningRate node not found in graph"
    assert biasone_nodes, "BiasOne node not found in graph"
    lr = lr_nodes[0]
    b1 = biasone_nodes[0]
    lr_gx, lr_gy = engine2.get_grid_coords(lr)
    b1_gx, b1_gy = engine2.get_grid_coords(b1)
    assert b1_gx == lr_gx + 1, f"BiasOne gx {b1_gx} not offset +1 from LR gx {lr_gx}"
    assert b1_gy == lr_gy, f"BiasOne gy {b1_gy} not equal to LR gy {lr_gy}"

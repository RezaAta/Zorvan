from ComputationalGraphs.GUI.examples_loader import ExamplesLoader

loader = ExamplesLoader()
for c in loader.get_categories():
    print(c.name)
    for e in c.examples:
        print(" -", e[0])

print("\nAttempt to build the piecewise MLP example:")
for cat in loader.get_categories():
    for name, desc, fn in cat.examples:
        if name.startswith("Piecewise Function MLP"):
            print("Building example:", name)
            g = fn()
            print("Nodes:", len(g.nodes))
            print("Starting nodes:", [n.name for n in g.starting_nodes])
            print(
                "Hidden activations:", [h[1].name for h in g._mlp_graph.hiddenLayers[0]]
            )

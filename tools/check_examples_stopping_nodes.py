from gui_framework.legacy import ExamplesLoader

loader = ExamplesLoader()
# Find the forward-processing NN category
for cat in loader.get_categories():
    if cat.name.startswith("Neural Networks - Forward Processing"):
        for name, desc, builder in cat.examples:
            if name.startswith("XOR"):
                g = builder()
                stopping = getattr(g, "stopping_nodes", None)
                print("Example:", name)
                if stopping is None:
                    print("  stopping_nodes: None")
                else:
                    print("  stopping_nodes count:", len(stopping))
                    print("  names:", [n.name for n in stopping])
                break

from gui_framework.legacy import ExamplesLoader


def build_anfis():
    loader = ExamplesLoader()
    for cat in loader.get_categories():
        if cat.name == "Fuzzy Systems":
            for name, desc, builder in cat.examples:
                if name.startswith("ANFIS XOR"):
                    print("Found example:", name)
                    g = builder()
                    print("Graph built with", len(g.nodes), "nodes")


if __name__ == "__main__":
    build_anfis()

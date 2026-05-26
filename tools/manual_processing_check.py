from gui_framework.legacy import ExamplesLoader
from zorvan.Core.GraphProcessor import GraphProcessor

if __name__ == "__main__":
    loader = ExamplesLoader()
    cat = loader.categories.get("neural_networks_manual")
    print("Manual category name:", cat.name)
    name, desc, builder = cat.examples[0]
    print("Building example:", name)
    graph = builder()
    print(
        "Graph built. Steps in manual sequence:",
        len(getattr(graph, "manual_processing_sequence", [])),
    )
    proc = GraphProcessor(graph, max_workers=1, verbose=False)
    proc.ManualProcessing(
        iterations=3,
        computation_sequence=getattr(graph, "manual_processing_sequence", None),
    )
    print("Manual processing completed.")

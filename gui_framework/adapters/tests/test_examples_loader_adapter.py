from gui_framework.adapters.examples_loader_adapter import ExamplesLoaderAdapter
from gui_framework.events.bus import EventType, get_event_bus
from gui_framework.services.examples_repository import ExamplesRepository

from zorvan.Core.Graph import Graph


class DummyMainWindow:
    def __init__(self, repository, examples_loader=None):
        self.examples_repository = repository
        self.examples_loader = examples_loader
        self.graph = None
        self.visualized = None

    def set_graph(self, graph):
        self.graph = graph

    def _visualize_graph_on_canvas(self, graph):
        self.visualized = graph


class DummyExampleLoader:
    def load_example(self, example_name):
        if example_name == "legacy_demo":
            return Graph()
        return None


def test_examples_loader_adapter_lists_examples_from_repository():
    repository = ExamplesRepository()
    repository.list_examples = lambda: {
        "demo": (lambda: Graph(), "Demo example"),
        "sample": (lambda: Graph(), "Sample example"),
    }
    main_window = DummyMainWindow(repository=repository)

    adapter = ExamplesLoaderAdapter(main_window)

    examples = adapter.list_examples()

    assert examples["demo"][0] == "demo"
    assert examples["demo"][1] == "Demo example"
    assert examples["sample"][0] == "sample"


def test_examples_loader_adapter_groups_examples_by_category():
    repository = ExamplesRepository()
    repository.list_examples_by_category = lambda: {
        "Prog": [("demo", "Demo example", lambda: Graph())],
        "MLP": [("xor", "XOR example", lambda: Graph())],
    }
    main_window = DummyMainWindow(repository=repository)

    adapter = ExamplesLoaderAdapter(main_window)

    grouped = adapter.list_examples_by_category()

    assert grouped["Prog"] == [("demo", "Demo example")]
    assert grouped["MLP"] == [("xor", "XOR example")]


def test_examples_loader_adapter_build_example_publishes_and_applies_graph():
    bus = get_event_bus()
    events = []

    def on_loaded(event):
        events.append(event)

    bus.subscribe(EventType.GRAPH_LOADED, on_loaded)

    try:
        graph = Graph()
        repository = ExamplesRepository()
        repository.build = lambda name: graph if name == "demo" else None
        main_window = DummyMainWindow(repository=repository, examples_loader=DummyExampleLoader())

        adapter = ExamplesLoaderAdapter(main_window)

        assert adapter.build_example("demo") is True
        assert main_window.graph is graph
        assert main_window.visualized is graph
        assert events and events[-1].payload["example_name"] == "demo"
        assert events[-1].payload["graph"] is graph
    finally:
        bus.unsubscribe(EventType.GRAPH_LOADED, on_loaded)


def test_examples_loader_adapter_legacy_load_example_uses_legacy_loader():
    repository = ExamplesRepository()
    main_window = DummyMainWindow(repository=repository, examples_loader=DummyExampleLoader())

    adapter = ExamplesLoaderAdapter(main_window)

    assert adapter.load_legacy_example("legacy_demo") is True
    assert isinstance(main_window.graph, Graph)
    assert main_window.visualized is main_window.graph

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel
from zorvan.Nodes.PopulationNode import PopulationNode


def test_population_node_exposes_expected_parameters_and_actions():
    node = PopulationNode(
        name="Pop", size=5, genome_length=3, lower_bound=-1.0, upper_bound=1.0
    )
    vm = NodeEditorViewModel(node)
    vm.initialize()

    props = vm.get_properties()
    # Expect at least genome_length and lower_bound/upper_bound
    assert "genome_length" in props
    assert "lower_bound" in props

    actions = vm.get_actions()
    assert "regenerate_population" in actions or "get_population_stats" in actions


def test_editable_parameters_whitelist():
    class Dummy:
        def __init__(self, name="d", count=10, config=None):
            self.name = name
            self.count = count
            self.data = {"a": 1}
            self._hidden = 5
            self.callable_attr = lambda x: x

    d = Dummy()
    vm = NodeEditorViewModel(d)
    vm.initialize()
    props = vm.get_properties()
    assert "name" in props
    assert "count" in props
    assert "data" in props
    assert "_hidden" not in props
    assert "callable_attr" not in props


def test_set_parameter_parses_list_strings():
    class Dummy:
        def __init__(self):
            self.name = "d"
            self.values = [1, 2]

    d = Dummy()
    vm = NodeEditorViewModel(d)
    vm.initialize()

    props = vm.get_properties()
    assert isinstance(props.get("values"), list)

    # Bracket style
    assert vm.set_parameter("values", "[3, 4]")
    assert d.values == [3, 4]

    # Comma-split style with numeric items
    assert vm.set_parameter("values", "5,6,7")
    assert d.values == [5, 6, 7]

    # Comma-split style with string items
    assert vm.set_parameter("values", "a, b, c")
    assert d.values == ["a", "b", "c"]

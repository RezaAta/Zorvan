from gui_framework.legacy import create_node
from gui_framework.legacy import get_short_name


def test_short_name_initializable_container():
    assert get_short_name("InitializableContainerNode") == "InitC"


def test_factory_creates_nodes():
    # Ensure factory can create these nodes
    for t in [
        "PopulationNode",
        "SingleInputCrossover",
        "LinearNodeDerivative",
        "InitializableContainerNode",
        "DisplayNode",
    ]:
        node = create_node(t, name_hint=f"test_{t}")
        assert node is not None, f"Factory should create {t}"

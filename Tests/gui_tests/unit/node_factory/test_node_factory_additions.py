def test_elitism_node_registered_and_creatable():
    from gui_framework.legacy import create_node, is_registered

    assert is_registered("ElitismNode") is True
    n = create_node("ElitismNode", name_hint="test")
    assert n is not None
    assert getattr(n, "name", "").startswith("Elitism")


def test_linear_derivative_name_not_duplicated():
    from gui_framework.legacy import create_node

    n = create_node("LinearNodeDerivative", name_hint="Linear'")
    assert n is not None
    assert getattr(n, "name", None) == "Linear'"


def test_elitism_factory_name_sanitized():
    from gui_framework.legacy import create_node

    # If name_hint is derived from class name (ElitismNode), the created name
    # should be 'Elitism' (or a variant) and NOT 'Elitism_ElitismNode'
    n = create_node("ElitismNode", name_hint="ElitismNode")
    assert n is not None
    nm = getattr(n, "name", "")
    assert "Elitism_ElitismNode" not in nm
    assert nm.startswith("Elitism")


def test_elitism_factory_name_with_prefix_hint():
    from gui_framework.legacy import create_node

    # If name_hint equals the prefix, we should get the prefix only
    n = create_node("ElitismNode", name_hint="Elitism")
    assert n is not None
    assert getattr(n, "name", None) == "Elitism"

    # If name_hint is a suffix form like 'Elitism_1', keep it as-is
    n2 = create_node("ElitismNode", name_hint="Elitism_1")
    assert n2 is not None
    assert getattr(n2, "name", None) == "Elitism_1"

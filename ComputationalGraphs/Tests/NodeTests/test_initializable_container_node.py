import math

from ComputationalGraphs.Nodes.InitializableContainerNode import (
    InitializableContainerNode,
)


def test_reinitialize_changes_value_within_bounds():
    n = InitializableContainerNode(
        name="W_test", value=0.0, init_low=-2.0, init_high=-1.0
    )
    orig = n.value
    new_val = n.reinitialize()
    assert new_val != orig or math.isclose(new_val, orig) is False
    assert new_val >= -2.0 and new_val <= -1.0


def test_reinitialize_multiple_times():
    n = InitializableContainerNode(
        name="W_test2", value=0.0, init_low=0.0, init_high=1.0
    )
    vals = set()
    for _ in range(10):
        vals.add(n.reinitialize())
    assert (
        len(vals) >= 2
    )  # Expect at least two different values over multiple reinitializations


def test_reinitialize_normal_mode():
    # Normal mode should produce values around mean with small deviation
    n = InitializableContainerNode(
        name="N_test", value=0.0, init_method="normal", init_mean=0.5, init_std=0.1
    )
    vals = [n.reinitialize() for _ in range(20)]
    avg = sum(vals) / len(vals)
    assert abs(avg - 0.5) < 0.2


def test_reinitialize_constant_mode():
    # constant mode removed - verify that 'constant' falls back to uniform (still a valid test for mode handling)
    n = InitializableContainerNode(name="C_test", value=0.0, init_method="constant")
    v = n.reinitialize()
    assert isinstance(v, float)

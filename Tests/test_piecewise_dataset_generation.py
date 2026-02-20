import math

import numpy as np

from zorvan.GUI.examples_loader import ExamplesLoader


def assert_equal_region_counts(xvals):
    n_total = len(xvals)
    n_regions = 3
    base = n_total // n_regions
    extra = n_total % n_regions
    expected_counts = [base + (1 if i < extra else 0) for i in range(n_regions)]

    c1 = sum(1 for x in xvals if x <= -1.0)
    c2 = sum(1 for x in xvals if (-1.0 < x) and (x < 1.0))
    c3 = sum(1 for x in xvals if x >= 1.0)

    assert (c1, c2, c3) == tuple(expected_counts)


def test_piecewise_mlp_concurrent_distribution():
    loader = ExamplesLoader()
    g = loader._build_piecewise_mlp_concurrent()
    mlp = getattr(g, "_mlp_graph", None)
    assert mlp is not None
    xvals = mlp.inputLayer[0][0].data
    assert min(xvals) >= -3.0
    assert max(xvals) <= 3.0
    assert_equal_region_counts(xvals)
    # ensure -1 belongs to the first region (<= -1)
    assert any(math.isclose(x, -1.0, rel_tol=0, abs_tol=1e-12) for x in xvals)
    # Check f(-1) == (-1)^2 == 1
    idx = next(
        i
        for i, x in enumerate(xvals)
        if math.isclose(x, -1.0, rel_tol=0, abs_tol=1e-12)
    )
    # Access the labels array attached to the MLP graph
    labels = mlp.labelLayer[0].data
    assert labels[idx] == 1.0
    # ensure 1 belongs to third region (>= 1) and maps to f(1) == 2
    assert any(math.isclose(x, 1.0, rel_tol=0, abs_tol=1e-12) for x in xvals)
    idx1 = next(
        i for i, x in enumerate(xvals) if math.isclose(x, 1.0, rel_tol=0, abs_tol=1e-12)
    )
    assert labels[idx1] == 2.0


def test_piecewise_mlp2_concurrent_distribution():
    loader = ExamplesLoader()
    g = loader._build_piecewise_mlp2_concurrent()
    mlp = getattr(g, "_mlp_graph", None)
    assert mlp is not None
    xvals = mlp.inputLayer[0][0].data
    assert min(xvals) >= -3.0
    assert max(xvals) <= 3.0
    assert_equal_region_counts(xvals)
    # ensure -1 belongs to the first region (<= -1)
    assert any(math.isclose(x, -1.0, rel_tol=0, abs_tol=1e-12) for x in xvals)
    # Check f(-1) == (-1)^2 == 1
    idx = next(
        i
        for i, x in enumerate(xvals)
        if math.isclose(x, -1.0, rel_tol=0, abs_tol=1e-12)
    )
    labels = mlp.labelLayer[0].data
    assert labels[idx] == 1.0
    # ensure 1 belongs to third region (>=1) and maps to f(1) == 2
    assert any(math.isclose(x, 1.0, rel_tol=0, abs_tol=1e-12) for x in xvals)
    idx1 = next(
        i for i, x in enumerate(xvals) if math.isclose(x, 1.0, rel_tol=0, abs_tol=1e-12)
    )
    assert labels[idx1] == 2.0

# Python reference baseline

Date: 2026-11-20 · Environment: Windows 10, Python 3.11.9, NumPy 2.0.2

Run from the repository root after `python -m pip install -e .`:

```powershell
python benchmarks/benchmark_xor.py --iterations 5000 --output benchmarks/xor_result.json
python benchmarks/benchmark_scaling.py --output benchmarks/scaling_result.json
```

## XOR MLP

The run used a 2-4-1 network, four XOR samples cycling one sample per
iteration, learning rate 0.1, and 5,000 processor iterations. Initial NumPy
weights and biases were copied from the seeded Python graph before timing.
Graph construction and model setup were excluded from both timers.

| Implementation | Time |
|---|---:|
| Python reference concurrent graph | 1.2675 s |
| NumPy scalar-sample training loop | 0.1309 s |
| Reference / NumPy | 9.68× |

This is a first local measurement, not a confirmation of the 3.91× historical
figure cited in the plan. The repository did not contain the original
benchmark script or environment details. The NumPy implementation uses the
same architecture, initial parameters, sample order, and learning rate, but
its update trace is not asserted equivalent to the concurrent graph's delayed
updates. Treat the ratio as a workload baseline, not an exact algorithmic
comparison. Raw output is in `xor_result.json`.

## Runtime scaling

`benchmark_scaling.py` measures an identity chain through 3 ticks and a
scalar-node 2-input, sigmoid-hidden, 1-output network at hidden widths 2–256.
The width benchmark constructs predecessor links directly and excludes graph
construction. This avoids the reference `Graph.AddNode()` dense adjacency
matrix, whose memory grows quadratically and prevents a useful 100,000-node
construction benchmark. The identity-chain benchmark likewise isolates
`GraphProcessor` using its `graph.nodes` interface. These microbenchmarks show
runtime growth, not end-to-end graph editing or training performance.

Selected measurements:

| Workload | Nodes | Ticks | Reference time | NumPy time | Ratio |
|---|---:|---:|---:|---:|---:|
| Identity chain | 100 | 3 | 0.00043 s | 0.000014 s | 31.6× |
| Identity chain | 1,000 | 3 | 0.00345 s | 0.000015 s | 227.3× |
| Identity chain | 10,000 | 3 | 0.04113 s | 0.000089 s | 462.7× |
| Identity chain | 100,000 | 3 | 0.42911 s | 0.000581 s | 738.3× |
| Hidden width 2 | 20 | 4 | 0.00024 s | 0.000092 s | 2.6× |
| Hidden width 32 | 260 | 19 | 0.00826 s | 0.000218 s | 37.9× |
| Hidden width 128 | 1,028 | 67 | 0.12238 s | 0.000465 s | 263.5× |
| Hidden width 256 | 2,052 | 131 | 0.49013 s | 0.001374 s | 356.6× |

The NumPy identity-chain work is a vectorized array shift, so those ratios are
not a like-for-like node operation comparison. Small timings are sensitive to
timer noise and should be rerun on the CI benchmark host before setting
regression thresholds. Full measurements are in `scaling_result.json`.

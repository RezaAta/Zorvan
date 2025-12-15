# Experiments Directory

Place reproducible experiment scripts and their small helper data here. This folder is excluded from pytest recursion to keep experiments and tests separate.

Guidelines:
- Include a short `README.md` explaining the experiment's purpose, how to run it, and the expected outputs.
- Use deterministic seeds and include options to limit runtime for quick iterations.
- Store generated outputs (plots, CSVs) under an `output/` folder that can be ignored by CI or cleared easily.

Example quick runner:

```python
# run.py
"""Simple entry point to run the experiment."""
if __name__ == '__main__':
    from Examples.Hybrid_Compare_Graph_vs_Classic import run_compare
    run_compare()
```

Reference experiments
- `HybridTempPredictionComparison.py`: compares concurrent Graph-based MLP+FIS vs `ClassicMLP` + FIS in closed-loop simulations. By default the closed-loop runs use a randomly chosen seed for initial conditions; the seed is printed when the experiment runs so results can be reproduced by re-running with that seed.

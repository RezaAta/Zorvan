import importlib.util

spec = importlib.util.spec_from_file_location(
    "htc", "Experiments/HybridTempPredictionComparison.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
res = mod.run_compare_once(master_seed=12345, verbose=False)
print("graph_metrics:", res["graph_metrics"])
print("classic_metrics:", res["classic_metrics"])
print("shared_seed:", res["shared_seed"])

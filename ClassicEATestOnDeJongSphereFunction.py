# Backwards-compatible shim for moved EA experiment
# The real implementation lives in Experiments/exp_ea_dejong_sphere.py

import importlib.util
import os
import sys

HERE = os.path.dirname(__file__)
TARGET = os.path.join(HERE, "..", "..", "..", "Experiments", "exp_ea_dejong_sphere.py")
TARGET = os.path.normpath(TARGET)

if os.path.exists(TARGET):
    spec = importlib.util.spec_from_file_location("exp_ea_dejong_sphere", TARGET)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Re-export commonly used functions
    evolve = getattr(module, "evolve")
    sphere_function = getattr(module, "sphere_function")
    run_graph_ea = (
        getattr(module, "run_graph_ea") if hasattr(module, "run_graph_ea") else None
    )
    # Deprecation warning
    print(
        "Warning: ClassicEATestOnDeJongSphereFunction.py has moved to Experiments/exp_ea_dejong_sphere.py"
    )
else:
    print(
        "Error: Could not locate moved EA experiment at Experiments/exp_ea_dejong_sphere.py"
    )
    raise ImportError("Missing Experiments/exp_ea_dejong_sphere.py")

import faulthandler
import importlib.util
import traceback
from pathlib import Path

faulthandler.enable(all_threads=True)
print("faulthandler enabled")

p = (
    Path(__file__).resolve().parents[1]
    / "Tests"
    / "test_apply_node_colors_clears_ann_override.py"
)
print("loading", p)
spec = importlib.util.spec_from_file_location("test_apply_node_colors", str(p))
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print("module loaded")
except Exception:
    traceback.print_exc()
    raise

try:
    print("Calling test function directly")
    mod.test_apply_node_colors_clears_ann_override()
    print("Function returned normally")
except Exception:
    print("Exception while running test function:")
    traceback.print_exc()

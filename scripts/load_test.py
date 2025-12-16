import importlib.util
import sys
import traceback

print("before loader")
spec = importlib.util.spec_from_file_location("t", "scripts/run_icon_hover_test.py")
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    print("module loaded OK")
except Exception:
    traceback.print_exc()
    sys.exit(1)

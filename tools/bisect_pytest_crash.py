"""
Bisect the test file list to find the smallest subset that triggers a crash (Windows AV).
Usage: python tools/bisect_pytest_crash.py

It will run pytest on subsets of test files and narrow down to a single file causing the crash.
"""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
# Collect candidate test files (*.py starting with test_ or under gui_tests/**)
test_files = sorted([str(p) for p in root.rglob("test_*.py")])
print(f"Found {len(test_files)} test files")


def run_subset(files):
    if not files:
        return False, 0
    cmd = [sys.executable, "-m", "pytest", "-q", "--maxfail=1"] + files
    print("Running", len(files), "files...")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    out_lines = []
    for line in proc.stdout:
        out_lines.append(line)
        print(line, end="")
    proc.wait()
    return proc.returncode != 0 and proc.returncode != 0, proc.returncode


lo = 0
hi = len(test_files)
# Quick check whether entire set crashes
crash, rc = run_subset(test_files)
print("Entire set crash?", crash, "rc=", rc)
if not crash:
    print("No crash for full set — nothing to bisect")
    sys.exit(0)

# Binary search for smallest crashing subset
l = 0
r = len(test_files)
crashing_files = test_files
while len(crashing_files) > 1:
    mid = len(crashing_files) // 2
    subset = crashing_files[:mid]
    crash, rc = run_subset(subset)
    if crash:
        crashing_files = subset
    else:
        crashing_files = crashing_files[mid:]

print("Suspect single file triggering crash:", crashing_files)

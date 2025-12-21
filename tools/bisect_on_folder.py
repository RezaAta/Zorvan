"""
Bisect test files within a given folder to find the subset that triggers crash.
Usage: python tools/bisect_on_folder.py ComputationalGraphs/Tests
"""

import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: bisect_on_folder.py <folder>")
    sys.exit(1)

folder = Path(sys.argv[1])
if not folder.exists():
    print("Folder does not exist:", folder)
    sys.exit(1)

test_files = sorted([str(p) for p in folder.rglob("test_*.py")])
print("Found", len(test_files), "test files under", folder)

import math


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


crash, rc = run_subset(test_files)
print("Full set crash?", crash, "rc=", rc)
if not crash:
    print("No crash in this folder")
    sys.exit(0)

crashing = test_files
while len(crashing) > 1:
    mid = len(crashing) // 2
    subset = crashing[:mid]
    crash, rc = run_subset(subset)
    if crash:
        crashing = subset
    else:
        crashing = crashing[mid:]

print("Suspect file(s):", crashing)

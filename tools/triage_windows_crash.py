"""
Triage helper to run the full test suite and capture logs to help identify Windows crashes.
Run locally on Windows to collect output and determine last test executed before crash.
"""

import subprocess
import sys
from pathlib import Path

log = Path("tmp_pytest_run.log")
cmd = [sys.executable, "-m", "pytest", "-q"]
print("Running:", " ".join(cmd))
with log.open("w", encoding="utf-8") as f:
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
    )
    for line in proc.stdout:
        f.write(line)
        f.flush()
        print(line, end="")
    proc.wait()
    print("Return code:", proc.returncode)

print("Wrote log to", log.absolute())

# Heuristic: find last line containing '::' and a test result marker
content = log.read_text(encoding="utf-8")
lines = content.splitlines()
last_test = None
for line in reversed(lines):
    if "::" in line and ("PASSED" in line or "FAILED" in line or "ERROR" in line):
        last_test = line
        break

print("Last test line found:", last_test)

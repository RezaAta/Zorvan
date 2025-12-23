#!/usr/bin/env python3
"""
Repro crash runner

Runs pytest (or an arbitrary pytest target) in a loop with faulthandler enabled
and optional Qt snapshot logging (via ENABLE_QT_SNAPSHOT env var used by the
project's conftest fixture). Captures stdout/stderr per iteration into
`artifacts/repro_runner/run_<n>/{stdout,stderr,qt_snapshot.txt}`.

Usage examples:
  python tools/repro_crash_runner.py --tests "gui_tests/unit" --loops 100 --snapshot
  python tools/repro_crash_runner.py --tests "gui_tests/unit/test_color_preferences_view.py::test_color_view_updates_buttons_and_applies" --loops 50

Notes:
- The runner invokes Python with `-X faulthandler` to enable the faulthandler
  C-level handler so that if a native crash happens some additional output
  may be printed to stderr.
- To get Qt snapshots set `--snapshot` (this sets ENABLE_QT_SNAPSHOT=1 for
  the pytest subprocess; the project's conftest listens to this variable).
- If a run fails with an exit code != 0 or stderr contains likely crash signs
  (e.g. 'Fatal Python error', 'Windows fatal exception', 'access violation')
  the runner will stop and preserve logs for inspection.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

EXIT_OK = 0
EXIT_FAIL = 1

LIKELY_CRASH_MARKERS = [
    "Fatal Python error",
    "Windows fatal exception",
    "access violation",
    "Segmentation fault",
    "EXCEPTION_ACCESS_VIOLATION",
]


def now_ts():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def run_once(run_index: int, args, out_dir: Path) -> tuple[int, Path]:
    run_dir = out_dir / f"run_{run_index:04d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Enable the project's optional qt snapshot fixture
    if args.snapshot:
        env["ENABLE_QT_SNAPSHOT"] = "1"

    # Build pytest command; use -X faulthandler via the interpreter
    cmd = [sys.executable, "-X", "faulthandler", "-m", "pytest"]
    cmd.extend(args.pytest_args)
    # Ensure quick failure detection
    if "-q" not in args.pytest_args and "--quiet" not in args.pytest_args:
        cmd.append("-q")
    if "--maxfail" not in " ".join(args.pytest_args):
        cmd.extend(["--maxfail=1"])
    cmd.append(args.tests)

    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"

    with stdout_path.open("wb") as out_f, stderr_path.open("wb") as err_f:
        print(f"[run {run_index}] -> {cmd}")
        proc = subprocess.Popen(cmd, env=env, stdout=out_f, stderr=err_f)
        try:
            proc.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            err_f.write(b"\n--- runner: timeout, killed process ---\n")

    # Copy optional qt state snapshot file if produced by the test run
    qt_snapshot_src = Path("qt_state_log.txt")
    if qt_snapshot_src.exists():
        shutil.copy2(qt_snapshot_src, run_dir / "qt_state_log.txt")

    return proc.returncode, run_dir


def looks_like_crash(stderr_text: str) -> bool:
    lower = stderr_text.lower()
    for marker in LIKELY_CRASH_MARKERS:
        if marker.lower() in lower:
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Repro crash runner for GUI tests")
    parser.add_argument(
        "--tests",
        default="gui_tests/unit",
        help="Pytest target to run (dir, file or nodeid)",
    )
    parser.add_argument(
        "--loops", type=int, default=50, help="Number of iterations to run"
    )
    parser.add_argument(
        "--snapshot", action="store_true", help="Enable ENABLE_QT_SNAPSHOT for each run"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Seconds to wait per run before killing",
    )
    parser.add_argument(
        "--out", default="artifacts/repro_runner", help="Output directory for logs"
    )
    parser.add_argument(
        "--pytest-args",
        dest="pytest_args",
        default=[],
        nargs="*",
        help="Additional args passed to pytest (quoted as needed)",
    )
    parser.add_argument(
        "--sleep", type=float, default=1.0, help="Seconds to sleep between runs"
    )

    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "start_time": now_ts(),
        "tests": args.tests,
        "loops": args.loops,
        "timestamp": now_ts(),
    }

    print("Repro runner starting")
    print(summary)

    for i in range(1, args.loops + 1):
        print(f"\n=== Iteration {i}/{args.loops} ===")
        retcode, run_dir = run_once(i, args, out_dir)

        # Read stderr to detect likely crash markers
        stderr_path = run_dir / "stderr.txt"
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="ignore")

        if retcode != 0:
            print(
                f"[run {i}] pytest exited with code {retcode}; inspecting stderr for crash markers..."
            )
            if looks_like_crash(stderr_text):
                print(
                    f"[run {i}] Detected likely crash marker in stderr; stopping further runs."
                )
                print(f"Logs saved to: {run_dir.resolve()}")
                print("Copy or upload the run directory for analysis.")
                return EXIT_FAIL
            else:
                print(
                    f"[run {i}] Non-zero exit but no crash markers detected; continuing (logs at {run_dir.resolve()})."
                )
        else:
            print(f"[run {i}] OK (exit 0)")

        # If a snapshot file exists, print its top lines for quick inspection
        snapshot_path = run_dir / "qt_state_log.txt"
        if snapshot_path.exists():
            try:
                print("qt_state_log.txt preview:")
                print(
                    "\n".join(
                        snapshot_path.read_text(
                            encoding="utf-8", errors="ignore"
                        ).splitlines()[:20]
                    )
                )
            except Exception:
                pass

        time.sleep(args.sleep)

    print("\nAll runs completed without detecting crash markers.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())

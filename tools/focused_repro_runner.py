#!/usr/bin/env python3
"""
Focused reproducer runner

Runs one or more pytest node ids repeatedly with faulthandler enabled and optional
Qt snapshot logging. Writes each run's stdout/stderr and preserves exit codes.

Usage example:
  python tools/focused_repro_runner.py --loops 200 "gui_tests/unit/test_collapsible_section_viewmodel.py::TestCollapsibleSectionViewModel::test_has_store_and_event_bus" "gui_tests/unit/test_color_preferences_view.py::test_color_view_updates_buttons_and_applies" --snapshot

"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

LIKELY_CRASH_MARKERS = [
    "Fatal Python error",
    "Windows fatal exception",
    "access violation",
    "Segmentation fault",
    "EXCEPTION_ACCESS_VIOLATION",
]


def now_ts():
    import datetime

    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def looks_like_crash(stderr_text: str) -> bool:
    lower = stderr_text.lower()
    for marker in LIKELY_CRASH_MARKERS:
        if marker.lower() in lower:
            return True
    return False


def run_once(run_index: int, tests: list[str], args, out_dir: Path) -> tuple[int, Path]:
    run_dir = out_dir / f"run_{run_index:04d}"
    run_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if args.snapshot:
        env["ENABLE_QT_SNAPSHOT"] = "1"

    cmd = [sys.executable, "-X", "faulthandler", "-m", "pytest", "-q", "--maxfail=1"]
    cmd.extend(tests)

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

    # copy global qt_state_log if present
    src = Path("gui_tests/unit/qt_state_log.txt")
    if src.exists():
        try:
            (run_dir / "qt_state_log.txt").write_bytes(src.read_bytes())
        except Exception:
            pass

    return proc.returncode, run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Focused repro runner for GUI tests")
    parser.add_argument("tests", nargs="+", help="One or more pytest nodeids to run")
    parser.add_argument("--loops", type=int, default=200)
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument(
        "--timeout", type=int, default=300, help="Seconds to wait per run"
    )
    parser.add_argument(
        "--out", default="artifacts/focused_repro", help="Output directory"
    )
    parser.add_argument(
        "--sleep", type=float, default=0.5, help="Seconds to sleep between runs"
    )

    args = parser.parse_args(argv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Focused repro runner starting", {"tests": args.tests, "loops": args.loops})

    for i in range(1, args.loops + 1):
        rc, run_dir = run_once(i, args.tests, args, out_dir)
        stderr_text = run_dir.joinpath("stderr.txt").read_text(errors="ignore")
        if rc != 0:
            print(
                f"[run {i}] pytest exited with code {rc}; checking for crash markers..."
            )
            if looks_like_crash(stderr_text):
                print(
                    f"[run {i}] Detected crash marker; stopping. Logs: {run_dir.resolve()}"
                )
                return 1
            else:
                print(
                    f"[run {i}] Failure but no crash marker; continuing. Logs: {run_dir.resolve()}"
                )
        else:
            print(f"[run {i}] OK")

        # quick preview
        try:
            if (run_dir / "qt_state_log.txt").exists():
                print("qt_state_log preview:")
                print((run_dir / "qt_state_log.txt").read_text().splitlines()[:20])
        except Exception:
            pass

        time.sleep(args.sleep)

    print("All iterations completed without crash markers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import os
import subprocess
import sys
from pathlib import Path

import pytest

MANUAL_TOOL_SCRIPTS = [
    "tools/test_apply_layout.py",
    "tools/test_auto_expand_canvas.py",
    "tools/test_backend_switch.py",
    "tools/test_enter_leave.py",
    "tools/test_node_editor_reinit.py",
    "tools/test_paste_at_cursor.py",
    "tools/test_paste_relative.py",
    "tools/test_plot_legend_uniqueness.py",
    "tools/test_qtawesome_icons.py",
    "tools/test_visualize_large_graph.py",
    "tools/test_wheel_event.py",
    "tools/manual_processing_check.py",
]


def _run_script(script_path: str) -> subprocess.CompletedProcess:
    repo_root = Path(__file__).resolve().parents[3]
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env["PYTHONPATH"] = str(repo_root)
    return subprocess.run(
        [sys.executable, script_path],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.mark.gui
def test_manual_tool_scripts_run_without_exceptions():
    pytest.importorskip("PyQt6")

    failures = []
    for script in MANUAL_TOOL_SCRIPTS:
        result = _run_script(script)
        if result.returncode != 0:
            failures.append((script, result.returncode, result.stdout, result.stderr))

    if failures:
        msgs = []
        for script, returncode, out, err in failures:
            msgs.append(
                f"{script} failed with code {returncode}\nSTDOUT:\n{out}\nSTDERR:\n{err}"
            )
        pytest.fail("\n\n".join(msgs))

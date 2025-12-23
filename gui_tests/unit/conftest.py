import pytest

# Session-scoped, autouse fixture to ensure a single QApplication exists for all
# GUI tests. Some tests create module-scoped qapp fixtures which can trigger
# Qt shutdown between modules and cause intermittent native crashes on Windows
# when later tests interact with non-GUI code. Keeping a global app alive for
# the whole pytest session avoids that tear-down and prevents spurious crashes.

try:
    from PyQt6.QtWidgets import QApplication

    @pytest.fixture(scope="session", autouse=True)
    def _global_qapp():
        app = QApplication.instance() or QApplication([])
        yield app
        # deliberately do not quit the app here to avoid tearing down Qt during
        # the test session. Let the process exit cleanly at the end of the run.

except Exception:
    # If PyQt6 is not available, tests that require it will be skipped by their
    # own markers; simply provide a no-op to keep pytest imports happy.
    @pytest.fixture(scope="session", autouse=True)
    def _global_qapp():
        yield None


# Debug helper: record Qt state snapshots before and after each test to help
# diagnose intermittent native crashes that occur during event processing.
try:
    import json
    import os
    import time

    LOG_PATH = os.path.join(os.path.dirname(__file__), "qt_state_log.txt")

    def _snapshot_qt_state(prefix: str):
        # Extremely conservative snapshot: avoid importing or calling any PyQt
        # APIs (those have caused native crashes during teardown). We only
        # record whether the probe was intentionally disabled and attempt a
        # completely safe registry probe via sys.modules if the module is
        # already loaded. This is intentionally minimal to avoid touching
        # C-level Qt code.
        widgets_info = "probe_disabled_for_safety"

        regs_info = "no_registry"
        try:
            import sys

            mod = sys.modules.get(
                "ComputationalGraphs.GUI.controllers.control_panel_builder"
            )
            if mod is not None and hasattr(mod, "_REGISTERED_ICON_BUTTONS"):
                try:
                    regs = getattr(mod, "_REGISTERED_ICON_BUTTONS") or []
                    regs_info = f"registered_count={len(regs)}"
                except Exception:
                    regs_info = "registered_unavailable"
        except Exception:
            regs_info = "no_registry"

        try:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(
                    f"=== {time.strftime('%Y-%m-%d %H:%M:%S')} {prefix} PYTEST_CURRENT_TEST={os.environ.get('PYTEST_CURRENT_TEST')} ===\n"
                )
                f.write(f"WidgetsInfo: {widgets_info}\n")
                f.write(f"RegistryInfo: {regs_info}\n\n")
        except Exception:
            pass

    @pytest.fixture(autouse=True)
    def _log_qt_state(request):
        # Enable only when explicitly requested to avoid interacting with Qt
        # during normal test runs which has proven to be fragile on Windows.
        enable = os.environ.get("ENABLE_QT_SNAPSHOT", "0") == "1"
        if not enable:
            yield
            return
        _snapshot_qt_state("before")
        yield
        _snapshot_qt_state("after")

        # Optional aggressive cleanup during repro runs: when enabled, attempt
        # to flush pending events and close/delete any top-level widgets to
        # prevent delayed events from running after a test and causing native
        # crashes. This is only active when ENABLE_QT_CLEANUP=1 is set in the
        # environment for repro sessions.
        try:
            do_cleanup = os.environ.get("ENABLE_QT_CLEANUP", "0") == "1"
            if do_cleanup:
                try:
                    from PyQt6.QtWidgets import QApplication

                    app = QApplication.instance()
                    if app is not None:
                        # Process any pending events first
                        app.processEvents()
                        # Close and schedule deletion for top-level widgets
                        for w in list(app.topLevelWidgets()):
                            try:
                                # Only operate on QWidget instances
                                if hasattr(w, "close"):
                                    try:
                                        w.close()
                                    except Exception:
                                        pass
                                try:
                                    w.setParent(None)
                                except Exception:
                                    pass
                                try:
                                    w.deleteLater()
                                except Exception:
                                    pass
                            except Exception:
                                pass
                        # Process events again to flush deletions
                        app.processEvents()
                except Exception:
                    pass
        except Exception:
            pass

except Exception:
    # If anything in the snapshot helper failed to initialize, disable it
    # silently so normal test runs are unaffected.
    pass

from gui_framework.legacy import MainWindow


def test_step_progress_bar_presence_and_updates():
    win = MainWindow()

    # Progress bar should exist and initially be 0
    assert hasattr(win, "step_progress")
    prog = win.step_progress
    assert prog.value() == 0

    # When Max Steps changes, the progress maximum should update
    win.max_steps_spin.setValue(20)
    assert prog.maximum() == 20
    # Simulate step completed
    win.graph_runner.is_running = True
    win.graph_runner.current_step = 4
    win.graph_runner.max_steps = 20
    win.execution_controller.on_step_completed(5)
    assert prog.value() == 5
    # The main step label should show current/max
    assert win.step_label.text() == "Step: 5 / 20"

    # Reset processor should reset progress and update label
    win.execution_controller.reset_processor()
    assert prog.value() == 0
    assert win.step_label.text() == "Step: 0 / 20"

    # The progress widget should be themed: chunk color should match accent
    from gui_framework.legacy import get_theme_manager

    tm = get_theme_manager()
    accent = tm.get_color("accent").name()
    # Style sheet should reference the accent color so the chunk is themed
    assert accent in prog.styleSheet()

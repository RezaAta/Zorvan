from ComputationalGraphs.GUI.controllers.execution_controller import ExecutionController


class DummyLabel:
    def __init__(self, text=""):
        self.text = text

    def setText(self, s):
        self.text = s


class DummyProgress:
    def __init__(self):
        self.max = None
        self.value = None

    def setMaximum(self, m):
        self.max = m

    def setValue(self, v):
        self.value = v


class DummySpin:
    def __init__(self, v=100):
        self._v = v

    def value(self):
        return self._v

    def interpretText(self):
        return None


class DummyCanvas:
    def update_node_visuals(self, *a, **k):
        self.updated = True

    def highlight_active_nodes(self, *a, **k):
        pass


class DummyGraphRunner:
    def __init__(self, is_running=False, current_step=0, max_steps=100):
        self.is_running = is_running
        self.current_step = current_step
        self.max_steps = max_steps
        self.processor_type = "concurrent"

    def get_processing_graph(self):
        return None


class DummyMain:
    def __init__(self, runner):
        self.graph_runner = runner
        self.step_label = DummyLabel("Step: 0 / 100")
        self.step_progress = DummyProgress()
        self.max_steps_spin = DummySpin(100)
        self.skip_visualization = False
        self.skip_plotting = False
        self.colorize_enabled = False
        self.canvas = DummyCanvas()
        # minimal check control
        self.dim_processed_check = type("X", (), {"isChecked": lambda self: False})()


def test_on_step_completed_ignores_stale_event_after_reset():
    runner = DummyGraphRunner(is_running=False, current_step=0, max_steps=100)
    mw = DummyMain(runner)
    ctrl = ExecutionController(mw)

    # Simulate a stale step event (e.g. emitted after stop/reset)
    ctrl.on_step_completed(5)

    # Step label should remain at 0 (unchanged)
    assert mw.step_label.text == "Step: 0 / 100"


def test_on_step_completed_updates_when_running():
    runner = DummyGraphRunner(is_running=True, current_step=4, max_steps=100)
    mw = DummyMain(runner)
    ctrl = ExecutionController(mw)

    ctrl.on_step_completed(5)

    assert mw.step_label.text == "Step: 5 / 100"
    assert mw.step_progress.value == 5
    assert mw.step_progress.max == 100

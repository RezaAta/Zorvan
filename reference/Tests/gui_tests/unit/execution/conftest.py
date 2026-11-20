import pytest

from gui_framework.events import bus as event_bus_module


@pytest.fixture(autouse=True)
def _reset_execution_event_bus():
    event_bus_module._bus = event_bus_module.EventBus()
    yield
    event_bus_module._bus = event_bus_module.EventBus()

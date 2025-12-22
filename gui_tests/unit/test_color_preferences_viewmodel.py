import pytest

from ComputationalGraphs.GUI.theme import get_theme_manager
from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import (
    ColorPreferencesViewModel,
)


def test_set_color_and_apply(tmp_path):
    tm = get_theme_manager()
    vm = ColorPreferencesViewModel()
    vm.initialize()

    # Set a color for a key without applying (apply_theme=False)
    vm.set_color_for_key("panel_bg", "#112233", apply_theme=False)
    assert vm.theme["panel_bg"] == "#112233"

    # Apply should call theme manager apply
    vm.on_apply()
    assert tm.theme.get("panel_bg") == "#112233" or tm.theme.get("bg") == "#112233"

    # Reset should restore defaults
    vm.on_reset()
    assert tm.theme.get("panel_bg") == tm.defaults.get("panel_bg")

    vm.cleanup()

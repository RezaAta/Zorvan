from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import (
    ColorPreferencesViewModel,
)


def test_viewmodel_named_theme_crud():
    vm = ColorPreferencesViewModel()
    name = "__vm_test_theme__"
    try:
        vm.delete_named_theme(name)
    except Exception:
        pass

    # Set some values on the vm theme and save
    vm.theme["panel_bg"] = "#abcdef"
    vm.theme["accent"] = "#333333"
    vm.save_named_theme(name)

    names = vm.get_named_themes()
    assert name in names

    # Apply as preview
    vm.apply_named_theme(name, persist=False)
    assert vm.get_color("panel_bg") == "#abcdef"

    # Persist selection
    vm.set_selected_theme_name(name, persist=True)
    assert vm.get_selected_theme_name() == name

    # Cleanup
    vm.delete_named_theme(name)
    assert name not in vm.get_named_themes()

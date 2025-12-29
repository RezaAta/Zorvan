from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import (
    ColorPreferencesViewModel,
)
from gui_framework.views.dialogs.color_preferences_dialog import ColorPreferencesDialog


def test_dialog_populates_named_themes():
    vm = ColorPreferencesViewModel()
    name = "__ui_test_theme__"
    try:
        vm.delete_named_theme(name)
    except Exception:
        pass

    vm.theme["panel_bg"] = "#555555"
    vm.save_named_theme(name)

    dlg = ColorPreferencesDialog(vm)
    try:
        dlg._populate_theme_combo()
        items = [dlg.theme_combo.itemText(i) for i in range(dlg.theme_combo.count())]
        assert name in items
    finally:
        try:
            dlg.close()
        except Exception:
            pass
        try:
            vm.delete_named_theme(name)
        except Exception:
            pass

import importlib
import traceback

print('theme import:')
try:
    from gui_framework.legacy.theme import get_theme_manager
    print('ok', get_theme_manager)
except Exception as e:
    print('theme import failed', repr(e))
    traceback.print_exc()

print('viewmodel import:')
try:
    from gui_framework.viewmodels.dialogs.color_preferences_viewmodel import ColorPreferencesViewModel
    print('ok viewmodel', ColorPreferencesViewModel)
except Exception as e:
    print('viewmodel import failed', repr(e))
    traceback.print_exc()

print('mvvm dialog import:')
try:
    from gui_framework.views.dialogs.color_preferences_dialog import ColorPreferencesDialog as MVVMColorDialog
    print('ok mvvm dialog', MVVMColorDialog)
except Exception as e:
    print('mvvm dialog import failed', repr(e))
    traceback.print_exc()

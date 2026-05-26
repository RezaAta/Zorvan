import importlib
try:
    import gui_framework.legacy.color_preferences as cp
    print('cp module loaded', cp)
    print('ColorPreferencesDialog', cp.ColorPreferencesDialog)
except Exception as e:
    import traceback
    print('import failed', repr(e))
    traceback.print_exc()

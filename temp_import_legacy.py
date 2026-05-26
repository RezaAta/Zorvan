import importlib
import sys
# Ensure fresh import environment
sys.modules.pop('gui_framework.legacy', None)
sys.modules.pop('gui_framework.legacy.color_preferences', None)
try:
    import gui_framework.legacy as legacy
    print('legacy ColorPreferencesDialog', legacy.ColorPreferencesDialog)
except Exception as e:
    import traceback
    print('legacy import failed', repr(e))
    traceback.print_exc()

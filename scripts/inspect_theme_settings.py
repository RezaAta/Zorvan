from zorvan.GUI.theme import get_theme_manager

m = get_theme_manager()
name = "__inspect_test__"
try:
    m.delete_named_theme(name)
except Exception:
    pass
m.save_named_theme(name, {"panel_bg": "#111111"})
print("names raw repr:", repr(m.settings.value("themes/names")))
print("list_named_themes():", m.list_named_themes())
try:
    m.settings.beginGroup("themes")
    print("themes childGroups:", m.settings.childGroups())
    m.settings.endGroup()
except Exception:
    pass
print("allKeys:", m.settings.allKeys()[:50])

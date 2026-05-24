from gui_framework.legacy import get_theme_manager


def test_theme_named_crud(tmp_path):
    tm = get_theme_manager()
    name = "__test_theme__"
    # Ensure clean start
    try:
        tm.delete_named_theme(name)
    except Exception:
        pass

    theme = {"panel_bg": "#123456", "accent": "#abcdef", "ui_font_family": "Arial"}
    tm.save_named_theme(name, theme)

    assert name in tm.list_named_themes()

    loaded = tm.load_named_theme(name)
    assert loaded.get("panel_bg") == "#123456"
    assert loaded.get("accent") == "#abcdef"

    tm.set_selected_theme(name, persist=True)
    assert tm.get_selected_theme_name() == name

    # Delete and ensure removal and selected cleared
    tm.delete_named_theme(name)
    assert name not in tm.list_named_themes()
    assert tm.get_selected_theme_name() != name


def test_theme_get_selected_none():
    tm = get_theme_manager()
    # Clear selection
    try:
        tm.set_selected_theme(None, persist=True)
    except Exception:
        pass
    assert tm.get_selected_theme_name() is None

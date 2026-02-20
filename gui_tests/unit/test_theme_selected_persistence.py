from zorvan.GUI.theme import ThemeManager, get_theme_manager


def test_selected_theme_persistence():
    tm = get_theme_manager()
    name = "__selected_persist__"
    try:
        tm.delete_named_theme(name)
    except Exception:
        pass

    theme = {"panel_bg": "#222222", "accent": "#444444"}
    tm.save_named_theme(name, theme)

    # Set selected and persist
    tm.set_selected_theme(name, persist=True)
    assert tm.get_selected_theme_name() == name

    # Simulate restart by forcing a new manager instance
    try:
        # Reset the module-level singleton
        import zorvan.GUI.theme as theme_mod

        if hasattr(theme_mod, "_manager"):
            try:
                theme_mod._manager = None
            except Exception:
                pass
    except Exception:
        pass

    tm2 = get_theme_manager()
    # tm2 should see the selected name; manager applies preview at startup
    assert tm2.get_selected_theme_name() == name

    # Cleanup
    tm2.delete_named_theme(name)
    try:
        tm2.set_selected_theme(None, persist=True)
    except Exception:
        pass


def test_delete_selected_clears_selection():
    tm = get_theme_manager()
    name = "__selected_delete__"
    try:
        tm.delete_named_theme(name)
    except Exception:
        pass
    tm.save_named_theme(name, {"panel_bg": "#121212"})
    tm.set_selected_theme(name, persist=True)

    assert tm.get_selected_theme_name() == name

    tm.delete_named_theme(name)
    assert tm.get_selected_theme_name() is None or tm.get_selected_theme_name() != name

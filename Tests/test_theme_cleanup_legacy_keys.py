from zorvan.GUI.theme import get_theme_manager


def test_save_theme_removes_legacy_keys(tmp_path, monkeypatch):
    tm = get_theme_manager()
    # Use a temporary QSettings backend to avoid interfering with global settings
    from PyQt6.QtCore import QSettings

    tmpfile = tmp_path / "theme_test.ini"
    tm.settings = QSettings(str(tmpfile), QSettings.Format.IniFormat)

    # Ensure legacy keys are present
    tm.settings.setValue("theme/dock_bg", "#111111")
    tm.settings.setValue("theme/list_bg", "#222222")

    # Save a new theme with panel_bg authoritative
    new_theme = {"panel_bg": "#333333", "text": "#aaaaaa"}
    tm.save_theme(new_theme)

    # Legacy keys should be removed
    assert tm.settings.value("theme/dock_bg") is None
    assert tm.settings.value("theme/list_bg") is None
    # panel_bg should be set
    assert tm.settings.value("theme/panel_bg") == "#333333"

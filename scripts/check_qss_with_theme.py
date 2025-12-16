import sys

from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from ComputationalGraphs.GUI.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)
# Try applying theme manager like run_gui.py does
try:
    from ComputationalGraphs.GUI import theme as theme_mod

    tm = theme_mod.get_theme_manager()
    # Debug: print template and fallback paths
    try:
        import os

        base_dir = os.path.dirname(theme_mod.__file__)
        template_path = os.path.join(base_dir, "styles_template.qss")
        fallback_path = os.path.join(base_dir, "styles.qss")
        print("template_path exists:", os.path.exists(template_path), template_path)
        print("fallback_path exists:", os.path.exists(fallback_path), fallback_path)
    except Exception as e:
        print("Error discovering paths:", e)

    # Inspect theme items for problematic types
    print("theme keys and types:")
    for k, v in tm.theme.items():
        print(k, type(v), repr(v)[:120])

    # Re-implement the apply_theme steps here to surface any exceptions
    import os

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            s = f.read()
        for k, v in tm.theme.items():
            s = s.replace("{{%s}}" % k, str(v))
        # Try to set app stylesheet and capture exceptions
        try:
            app.setStyleSheet(s)
            print("Manual apply: setStyleSheet succeeded")
        except Exception as e:
            print("Manual apply: setStyleSheet failed:", e)
    except Exception as e:
        print("Manual apply: reading/replacing failed:", e)

    ok = tm.apply_theme(app)
    print("tm.apply_theme returned:", ok)
except Exception as e:
    print("tm.apply_theme failed:", e)

window = MainWindow()
window.show()

ss = app.styleSheet() or "<empty>"
print("--- Application stylesheet (first 200 chars) ---")
print(ss[:200])
print("--- contains QPushButton:hover? ->", "QPushButton:hover" in ss)

control_panel = window.findChild(QWidget, "controlPanel")
print("control_panel found:", control_panel is not None)
if control_panel is not None:
    buttons = control_panel.findChildren(QPushButton)
    print(f"Found {len(buttons)} QPushButton(s) in control panel")
    for i, btn in enumerate(buttons[:30]):
        print(i, repr(btn.text()), "styleSheet=[" + btn.styleSheet() + "]")

window.close()
app.quit()

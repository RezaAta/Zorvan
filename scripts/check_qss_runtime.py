import sys

from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from ComputationalGraphs.GUI.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)
window = MainWindow()
window.show()

print("--- Application stylesheet (first 1000 chars) ---")
ss = app.styleSheet() or "<empty>"
print(ss[:1000])
print("--- contains QPushButton:hover? ->", "QPushButton:hover" in ss)

control_panel = window.findChild(QWidget, "controlPanel")
print("control_panel found:", control_panel is not None)
if control_panel is not None:
    buttons = control_panel.findChildren(QPushButton)
    print(f"Found {len(buttons)} QPushButton(s) in control panel")
    for i, btn in enumerate(buttons[:30]):
        print(
            i,
            repr(btn.text()),
            "objectName=",
            repr(btn.objectName()),
            "styleSheet=[" + btn.styleSheet() + "]",
        )

# Keep window open briefly so manual inspection possible when running interactively
# (When run from tests, this will exit immediately)
window.close()
app.quit()

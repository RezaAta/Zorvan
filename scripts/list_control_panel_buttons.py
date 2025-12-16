import sys

from PyQt6.QtWidgets import QApplication, QPushButton, QWidget

from ComputationalGraphs.GUI.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)
mw = MainWindow()
control_panel = mw.findChild(QWidget, "controlPanel")
buttons = control_panel.findChildren(QPushButton)
for i, btn in enumerate(buttons):
    print(i, repr(btn.objectName()), repr(btn.text()), repr(btn.styleSheet()))

mw.close()
app.quit()

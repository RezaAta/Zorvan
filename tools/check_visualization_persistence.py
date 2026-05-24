import sys

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

sys.path.insert(0, "..")
from gui_framework.legacy import MainWindow, get_theme_manager

app = QApplication.instance() or QApplication([])

mw = MainWindow()
vc = mw.visualization_controller

mw.min_gradient_color = QColor(1, 2, 3)
mw.max_gradient_color = QColor(4, 5, 6)
mw.default_node_color = QColor(7, 8, 9)
mw.default_text_color = QColor(10, 11, 12)

print("Before persist, tm.settings values:")
print(get_theme_manager().settings.value("visualization/min_gradient_color"))

vc.apply_node_colors()

print("After persist, tm.settings values:")
print(get_theme_manager().settings.value("visualization/min_gradient_color"))

# Create new MainWindow
mw2 = MainWindow()
print("New main window colors:")
print("min_gradient_color", mw2.min_gradient_color.name())
print("max_gradient_color", mw2.max_gradient_color.name())
print("default_node_color", mw2.default_node_color.name())
print("default_text_color", mw2.default_text_color.name())

sys.exit(0)

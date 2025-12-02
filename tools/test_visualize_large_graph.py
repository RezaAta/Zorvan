from PyQt6.QtWidgets import QApplication
import sys
sys.path.insert(0, r'c:/My Stuff/Uni & Research/Artificial Inteligence/Computational Graph/Implementations/ComputationalGraphs')
from ComputationalGraphs.GUI.examples_loader import ExamplesLoader
from ComputationalGraphs.GUI.main_window import MainWindow

app = QApplication(sys.argv)
loader = ExamplesLoader()
# Large example builder
try:
    g = loader._build_piecewise_mlp2_concurrent()
except Exception:
    g = loader.categories['basic'].examples[0][2]()

mw = MainWindow()

# set graph and visualize
mw.set_graph(g)
mw._visualize_graph_on_canvas(g)

# Print scene rect and center
rect = mw.canvas.scene.sceneRect()
print('Scene rect:', rect.left(), rect.right(), rect.top(), rect.bottom())
print('View center scene coords:', mw.canvas.mapToScene(mw.canvas.viewport().rect().center()))
print('Scene center', rect.center())

app.quit()

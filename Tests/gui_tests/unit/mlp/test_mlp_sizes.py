from PyQt6.QtWidgets import QApplication

from zorvan.GUI.mlp_dialog import MLPGeneratorDialog


def test_mlp_dialog_hidden_layer_sizes():
    app = QApplication.instance() or QApplication([])
    dlg = MLPGeneratorDialog()
    # Configure two hidden layers and set sizes
    dlg.num_hidden_layers.setValue(2)
    dlg._update_hidden_layer_sizes(2)
    dlg.hidden_layer_spinboxes[0].setValue(3)
    dlg.hidden_layer_spinboxes[1].setValue(5)

    # Generate MLP
    dlg._generate_mlp()
    g = dlg.get_graph()
    assert g is not None
    assert g.hiddenLayerSizes == [3, 5]

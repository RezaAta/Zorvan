from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class BackpropConfigViewModel(BaseViewModel):
    """ViewModel for BackpropConfigDialog.

    Exposes learning rate and an option to use forward-processing backprop.
    """

    learning_rate = ObservableProperty("learning_rate", default=0.01)
    use_forward = ObservableProperty("use_forward", default=False)

    def __init__(self, learning_rate: float = 0.01, use_forward: bool = False):
        super().__init__()
        self.learning_rate = float(learning_rate)
        self.use_forward = bool(use_forward)

    def set_learning_rate(self, lr: float):
        self.learning_rate = float(lr)

    def get_learning_rate(self) -> float:
        return float(self.learning_rate)

    def set_use_forward(self, val: bool):
        self.use_forward = bool(val)

    def get_use_forward(self) -> bool:
        return bool(self.use_forward)

    def create_snapshot(self):
        self._snapshot = (self.get_learning_rate(), self.get_use_forward())

    def reset_to_snapshot(self):
        if hasattr(self, "_snapshot") and self._snapshot is not None:
            lr, uf = self._snapshot
            self.learning_rate = float(lr)
            self.use_forward = bool(uf)

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

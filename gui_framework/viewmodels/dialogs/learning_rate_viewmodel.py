from typing import Optional

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class LearningRateViewModel(BaseViewModel):
    value = ObservableProperty("value", default=0.01)

    def __init__(self, value: Optional[float] = 0.01):
        super().__init__()
        self.value = float(value) if value is not None else 0.01

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def set_value(self, v: float):
        try:
            self.value = float(v)
        except Exception:
            pass

    def get_value(self) -> float:
        return float(self.value)

    def create_snapshot(self):
        self._snapshot = self.get_value()

    def reset_to_snapshot(self):
        if hasattr(self, "_snapshot"):
            self.set_value(self._snapshot)

    def apply_to_node(self, node):
        """Apply learning rate to a node-like object. Supports attributes 'value' or 'learning_rate'."""
        try:
            if hasattr(node, "learning_rate"):
                node.learning_rate = self.get_value()
            elif hasattr(node, "value"):
                node.value = self.get_value()
            else:
                # attempt set attribute 'value'
                setattr(node, "value", self.get_value())
            return True
        except Exception:
            return False

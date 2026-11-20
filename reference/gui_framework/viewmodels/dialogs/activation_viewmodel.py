from typing import List

from gui_framework.viewmodels.base import BaseViewModel, ObservableProperty


class ActivationViewModel(BaseViewModel):
    selected = ObservableProperty("selected", default=None)
    available = ObservableProperty("available", default=None)

    def __init__(self, available: List[str] = None, selected: str = None):
        super().__init__()
        self.available = list(available or ["Sigmoid", "ReLU", "Linear", "Tanh"])
        self.selected = selected

    def initialize(self):
        self._mark_initialized()

    def cleanup(self):
        pass

    def set_selected(self, name: str):
        if name in self.available:
            self.selected = name

    def get_selected(self) -> str:
        return self.selected

    def get_available(self) -> List[str]:
        return list(self.available)

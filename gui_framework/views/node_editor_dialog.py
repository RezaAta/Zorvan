try:
    from PyQt6.QtWidgets import (
        QDialog,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QVBoxLayout,
    )

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

from gui_framework.viewmodels.node_editor_viewmodel import NodeEditorViewModel

if HAS_PYQT:

    class NodeEditorDialog(QDialog):
        def __init__(self, vm: NodeEditorViewModel, parent=None):
            super().__init__(parent)
            self.vm = vm
            self.setWindowTitle("Node Editor")
            self.layout = QVBoxLayout(self)
            self.form = QFormLayout()
            self.layout.addLayout(self.form)
            self._widgets = {}

            # Container for action buttons (node-specific helpers)
            self._action_buttons = {}

            vm.observe_property("properties_changed", self._on_properties_changed)
            self._on_properties_changed(None, None)
            try:
                # Schedule a second refresh on the next event loop turn to catch any
                # actions that may have been registered after VM initialization.
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(0, lambda: self._on_properties_changed(None, None))
            except Exception:
                pass

            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(self._on_ok)
            self.layout.addWidget(ok_btn)

        def _on_properties_changed(self, old, new):
            # Rebuild form
            while self.form.rowCount() > 0:
                self.form.removeRow(0)
            self._widgets.clear()

            # Basic fields (support both older and newer VM APIs)
            try:
                name_val = self.vm.get_name()
            except Exception:
                name_val = self.vm.get_properties().get("name", "")
            name_editor = QLineEdit(name_val)
            self.form.addRow(QLabel("Name"), name_editor)
            self._widgets["name"] = name_editor

            try:
                value_val = self.vm.get_value()
            except Exception:
                value_val = str(self.vm.get_properties().get("value", ""))
            value_editor = QLineEdit(value_val)
            self.form.addRow(QLabel("Value"), value_editor)
            self._widgets["value"] = value_editor

            # Boolean flags
            # Unified Forced Batch control: single checkbox bound to VM if available, otherwise to legacy property
            try:
                fb = None
                try:
                    fb = self.vm.get_forced_batch()
                    bound_to_vm = True
                except Exception:
                    fb = None
                    bound_to_vm = False
                if fb is None:
                    fb = self.vm.get_properties().get("forcedBatchProcessing")
                    bound_to_vm = False

                from PyQt6.QtWidgets import QCheckBox

                fb_editor = QCheckBox("Forced Batch")
                fb_editor.setChecked(bool(fb))

                if bound_to_vm:
                    fb_editor.stateChanged.connect(
                        lambda st: self.vm.set_forced_batch(bool(st))
                    )
                else:
                    fb_editor.stateChanged.connect(
                        lambda st: self.vm.set_property(
                            "forcedBatchProcessing", bool(st)
                        )
                    )

                self.form.addRow(QLabel("Forced Batch"), fb_editor)
                self._widgets["forcedBatch"] = fb_editor
            except Exception:
                pass

            try:
                inc = self.vm.get_incremental()
                inc_editor = QPushButton(
                    "Incremental: ON" if inc else "Incremental: OFF"
                )
                inc_editor.setCheckable(True)
                inc_editor.setChecked(inc)
                inc_editor.clicked.connect(
                    lambda checked: self.vm.set_incremental(bool(checked))
                )
                self.form.addRow(QLabel("Incremental"), inc_editor)
                self._widgets["Incremental"] = inc_editor
            except Exception:
                # legacy: no incremental support
                pass

            # Parameters discovered by VM (fallback to generic properties for older VM)
            try:
                params = self.vm.get_parameters()
                # Remove legacy forcedBatchProcessing to avoid duplicate UI controls
                if isinstance(params, dict) and "forcedBatchProcessing" in params:
                    params = dict(params)
                    params.pop("forcedBatchProcessing", None)
            except Exception:
                props = self.vm.get_properties()
                # Exclude known header fields and legacy forcedBatchProcessing
                params = {
                    k: v
                    for k, v in props.items()
                    if k
                    not in ("name", "value", "description", "forcedBatchProcessing")
                }

            for k, v in params.items():
                editor = None
                try:
                    # Make certain fields explicit read-only based on name
                    readonly = k in (
                        "inputCount",
                        "id",
                        "midCalculation",
                        "midCalculationValue",
                    )

                    if isinstance(v, bool):
                        from PyQt6.QtWidgets import QCheckBox

                        editor = QCheckBox()
                        editor.setChecked(v)
                        # Disable editing if readonly is requested
                        if readonly:
                            editor.setEnabled(False)
                        else:
                            editor.stateChanged.connect(
                                lambda st, name=k: (
                                    self.vm.set_parameter(name, bool(st))
                                    if hasattr(self.vm, "set_parameter")
                                    else self.vm.set_property(name, bool(st))
                                )
                            )
                    elif isinstance(v, int):
                        from PyQt6.QtWidgets import QSpinBox

                        editor = QSpinBox()
                        editor.setValue(v)
                        if readonly:
                            editor.setEnabled(False)
                        else:
                            editor.valueChanged.connect(
                                lambda val, name=k: (
                                    self.vm.set_parameter(name, int(val))
                                    if hasattr(self.vm, "set_parameter")
                                    else self.vm.set_property(name, int(val))
                                )
                            )
                    elif isinstance(v, float):
                        from PyQt6.QtWidgets import QDoubleSpinBox

                        editor = QDoubleSpinBox()
                        editor.setValue(v)
                        if readonly:
                            editor.setEnabled(False)
                        else:
                            editor.valueChanged.connect(
                                lambda val, name=k: (
                                    self.vm.set_parameter(name, float(val))
                                    if hasattr(self.vm, "set_parameter")
                                    else self.vm.set_property(name, float(val))
                                )
                            )
                    else:
                        # For lists (e.g., inputs), show a comma-separated editable field
                        if isinstance(v, (list, tuple)) and k == "inputs":
                            editor = QLineEdit(
                                ",".join([str(x) for x in v]) if v else ""
                            )
                            if readonly:
                                editor.setReadOnly(True)
                            else:

                                def _on_inputs_text(text, name=k):
                                    items = (
                                        [t.strip() for t in text.split(",")]
                                        if text
                                        else []
                                    )
                                    try:
                                        if hasattr(self.vm, "set_parameter"):
                                            self.vm.set_parameter(name, items)
                                        else:
                                            self.vm.set_property(name, items)
                                    except Exception:
                                        pass

                                editor.textChanged.connect(_on_inputs_text)
                        else:
                            editor = QLineEdit(str(v))
                            if readonly:
                                editor.setReadOnly(True)
                            else:
                                editor.textChanged.connect(
                                    lambda text, name=k: (
                                        self.vm.set_parameter(name, text)
                                        if hasattr(self.vm, "set_parameter")
                                        else self.vm.set_property(name, text)
                                    )
                                )
                except Exception:
                    editor = QLineEdit(str(v))
                    editor.textChanged.connect(
                        lambda text, name=k: (
                            self.vm.set_parameter(name, text)
                            if hasattr(self.vm, "set_parameter")
                            else self.vm.set_property(name, text)
                        )
                    )
                self.form.addRow(QLabel(k), editor)
                self._widgets[k] = editor

            # Actions
            try:
                # Remove previous action widgets
                if hasattr(self, "_actions_layout"):
                    try:
                        for i in reversed(range(self._actions_layout.count())):
                            w = self._actions_layout.itemAt(i).widget()
                            if w is not None:
                                w.setParent(None)
                    except Exception:
                        pass
                from PyQt6.QtWidgets import QHBoxLayout

                actions = (
                    self.vm.get_actions() if hasattr(self.vm, "get_actions") else {}
                )
                if actions:
                    self._actions_layout = QHBoxLayout()
                    for label in actions:
                        btn = QPushButton(label)
                        btn.clicked.connect(lambda _, name=label: self._on_action(name))
                        self._actions_layout.addWidget(btn)
                        self._action_buttons[label] = btn
                    self.layout.addLayout(self._actions_layout)
                # If actions were added to VM after initial pass (race), attempt a second
                # synchronous check to guarantee buttons exist for synchronous tests.
                try:
                    actions_late = (
                        self.vm.get_actions() if hasattr(self.vm, "get_actions") else {}
                    )
                    if not self._action_buttons and actions_late:
                        self._actions_layout = QHBoxLayout()
                        for label in actions_late:
                            btn = QPushButton(label)
                            btn.clicked.connect(
                                lambda _, name=label: self._on_action(name)
                            )
                            self._actions_layout.addWidget(btn)
                            self._action_buttons[label] = btn
                        self.layout.addLayout(self._actions_layout)
                except Exception:
                    pass
            except Exception:
                pass

        def _on_action(self, name: str):
            try:
                res = (
                    self.vm.call_action(name)
                    if hasattr(self.vm, "call_action")
                    else None
                )
                # If action returns stats, show them in a small dialog
                if isinstance(res, dict):
                    from PyQt6.QtWidgets import QMessageBox

                    text = "\n".join([f"{k}: {v}" for k, v in res.items()])
                    QMessageBox.information(self, f"{name} result", text)
            except Exception:
                pass

        def _on_ok(self) -> None:
            # Sync widget values back to VM
            try:
                if "name" in self._widgets:
                    self.vm.set_name(self._widgets["name"].text())
                if "value" in self._widgets:
                    self.vm.set_value(self._widgets["value"].text())

                # Parameters: read values based on widget type
                for k, w in list(self._widgets.items()):
                    if k in ("name", "value", "forcedBatch", "Incremental"):
                        continue
                    try:
                        if hasattr(w, "isChecked"):
                            self.vm.set_parameter(k, bool(w.isChecked()))
                        elif hasattr(w, "value"):
                            self.vm.set_parameter(k, w.value())
                        else:
                            self.vm.set_parameter(k, w.text())
                    except Exception:
                        pass

                # Call VM apply
                self.vm.apply_to_node()
            except Exception:
                pass
            super().accept()

else:

    class NodeEditorDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use NodeEditorDialog")

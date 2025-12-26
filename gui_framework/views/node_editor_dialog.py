try:
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import (
        QDialog,
        QFormLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QVBoxLayout,
    )

    HAS_PYQT = True
except Exception:
    HAS_PYQT = False

import logging

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

            # Use a debounced scheduler for rebuilds to avoid multiple queued rebuilds
            # which can delete widgets while they're still in use by external callers.
            self._rebuild_scheduled = False

            def _schedule_rebuild():
                # Avoid scheduling if already pending
                if getattr(self, "_rebuild_scheduled", False):
                    return
                self._rebuild_scheduled = True
                try:
                    QTimer.singleShot(0, _run_rebuild)
                except Exception:
                    # Fall back to immediate call (tests may run without full Qt event loop)
                    _run_rebuild()

            def _run_rebuild():
                self._rebuild_scheduled = False
                try:
                    self._on_properties_changed(None, None)
                except Exception:
                    pass

            vm.observe_property(
                "properties_changed", lambda old, new: _schedule_rebuild()
            )
            # Perform an initial synchronous build so tests can access widgets immediately
            # (we also schedule a second deferred rebuild just in case actions register later).
            self._on_properties_changed(None, None)
            try:
                # Schedule a second refresh on the next event loop turn to catch any
                # actions that may have been registered after VM initialization.
                from PyQt6.QtCore import QTimer

                QTimer.singleShot(0, lambda: _schedule_rebuild())
            except Exception:
                pass

            ok_btn = QPushButton("OK")
            ok_btn.clicked.connect(self._on_ok)
            self.layout.addWidget(ok_btn)

        def _adjust_textedit_height(self, editor, min_h=50, max_h=300):
            """Adjust the height of a QTextEdit to fit its content between min_h and max_h."""
            try:
                # Estimate height by number of blocks (lines) and font metrics
                doc = editor.document()
                block_count = doc.blockCount() or 1
                fm = editor.fontMetrics()
                line_height = fm.lineSpacing()
                new_height = int(block_count * line_height + 12)
                new_height = max(min_h, min(max_h, new_height))
                editor.setFixedHeight(new_height)
            except Exception:
                pass

        def _on_properties_changed(self, old, new):
            # Rebuild form
            # Preserve current widget textual values so user edits are not lost on refresh
            prev_values = {}
            for k, w in list(self._widgets.items()):
                try:
                    if hasattr(w, "toPlainText"):
                        prev_values[k] = w.toPlainText()
                    elif hasattr(w, "text"):
                        prev_values[k] = w.text()
                    elif hasattr(w, "value"):
                        prev_values[k] = str(w.value())
                    elif hasattr(w, "isChecked"):
                        prev_values[k] = str(w.isChecked())
                except Exception:
                    pass

            # Save previous widgets so we can reuse them in-place when possible.
            prev_widgets = dict(self._widgets)

            # Detach previous widgets from their parents so they are not deleted when
            # the layout is cleared. This keeps Python references alive for external
            # callers that may still hold references (e.g., tests using widget.stepBy()).
            for w in list(prev_widgets.values()):
                try:
                    w.setParent(None)
                except Exception:
                    pass

            while self.form.rowCount() > 0:
                self.form.removeRow(0)
            # Do not delete existing widget objects — reuse them where appropriate
            self._widgets = {}

            # Basic fields (support both older and newer VM APIs)
            try:
                name_val = self.vm.get_name()
            except Exception:
                name_val = self.vm.get_properties().get("name", "")
            name_initial = prev_values.get("name", name_val)
            # Reuse existing name editor if present
            prev_name = prev_widgets.get("name")
            if prev_name is not None and hasattr(prev_name, "setText"):
                try:
                    name_editor = prev_name
                    name_editor.setText(name_initial)
                except Exception:
                    name_editor = QLineEdit(name_initial)
            else:
                name_editor = QLineEdit(name_initial)
            self.form.addRow(QLabel("Name"), name_editor)
            self._widgets["name"] = name_editor

            # Show node type directly below name (read-only, displayed as label)
            try:
                type_val = self.vm.get_properties().get("type", "")
            except Exception:
                type_val = ""
            from PyQt6.QtWidgets import QLabel as _QLabel

            prev_type = prev_widgets.get("type")
            if prev_type is not None and hasattr(prev_type, "setText"):
                try:
                    type_label = prev_type
                    type_label.setText(str(type_val))
                except Exception:
                    type_label = _QLabel(str(type_val))
            else:
                type_label = _QLabel(str(type_val))
            self.form.addRow(QLabel("Type"), type_label)
            self._widgets["type"] = type_label

            try:
                value_val = self.vm.get_value()
            except Exception:
                value_val = str(self.vm.get_properties().get("value", ""))
            # Use a large, scrollable text box for the value so users can inspect
            # potentially large arrays/buffers easily
            prev_value_widget = prev_widgets.get("value")
            value_editor = None
            if prev_value_widget is not None and hasattr(
                prev_value_widget, "setPlainText"
            ):
                try:
                    # Try to reuse the widget, but be robust against deleted underlying C++ object
                    prev_value_widget.blockSignals(True)
                    prev_value_widget.setPlainText(
                        prev_values.get("value", str(value_val))
                    )
                    try:
                        prev_value_widget.blockSignals(False)
                    except Exception:
                        pass
                    # Quick sanity check that the widget is still valid
                    try:
                        _ = prev_value_widget.isVisible()
                        value_editor = prev_value_widget
                    except Exception:
                        value_editor = None
                except Exception:
                    # Reuse failed, fall back to creating a fresh widget
                    value_editor = None
            if value_editor is None:
                value_editor = QTextEdit()
                value_editor.setPlainText(prev_values.get("value", str(value_val)))
            # Make the text box dynamic: allow growth to a max height but shrink when content is small
            from PyQt6.QtWidgets import QSizePolicy

            expanding_policy = getattr(QSizePolicy, "Expanding", None)
            if expanding_policy is None and hasattr(QSizePolicy, "Policy"):
                try:
                    expanding_policy = QSizePolicy.Policy.Expanding
                except Exception:
                    expanding_policy = 0
            min_policy = getattr(QSizePolicy, "Minimum", None)
            if min_policy is None and hasattr(QSizePolicy, "Policy"):
                try:
                    min_policy = QSizePolicy.Policy.Minimum
                except Exception:
                    min_policy = 0
            try:
                value_editor.setSizePolicy(expanding_policy, min_policy)
                value_editor.setMaximumHeight(300)
                value_editor.setMinimumHeight(50)
                # Adjust initial height to fit content
                try:
                    self._adjust_textedit_height(value_editor)
                except Exception:
                    pass
            except Exception:
                # Widget may have been deleted asynchronously — ignore and continue
                pass
            self.form.addRow(QLabel("Value"), value_editor)
            self._widgets["value"] = value_editor
            # Connect changes to adjust height dynamically
            try:
                value_editor.textChanged.connect(
                    lambda: self._adjust_textedit_height(value_editor)
                )
            except Exception:
                pass

            # More details collapsible section (hidden by default)
            # Implement deterministically (avoid swallowing failures silently)
            from PyQt6.QtWidgets import QWidget

            # Toggle handler for the more details section
            def _toggle_more_details_inner():
                try:
                    # Toggle based on current widget visibility so it works synchronously in tests
                    visible = not self._more_widget.isVisible()
                    self._more_widget.setVisible(visible)
                    self._more_button.setChecked(visible)
                    # Update arrow glyph
                    self._more_button.setText(
                        "More details ▾" if visible else "More details ▸"
                    )
                except Exception:
                    pass

            # Attach the bound handler as a method so tests can call it
            self._toggle_more_details = _toggle_more_details_inner

            self._more_button = QPushButton("More details ▸")
            self._more_button.setCheckable(True)
            self._more_button.setChecked(False)
            self._more_button.clicked.connect(self._toggle_more_details)

            self._more_widget = QWidget()
            self._more_layout = QFormLayout(self._more_widget)
            self._more_widget.setVisible(False)
            # Add placeholder widgets (updated when properties change)
            self._more_widgets_keys = [
                "gui_pos",
                "computationType",
                "batchSize",
                "id",
                "inputCount",
            ]
            from PyQt6.QtWidgets import QLabel as _QLabel
            from PyQt6.QtWidgets import QLineEdit as _QLineEdit

            for key in self._more_widgets_keys:
                # Make more-details values read-only in the UI.
                # Use a read-only QLineEdit for the `id` (test expects a read-only line edit)
                if key == "id":
                    w = _QLineEdit("")
                    w.setReadOnly(True)
                else:
                    w = _QLabel("")
                    # Display as disabled to clearly indicate readonly status
                    try:
                        w.setEnabled(False)
                    except Exception:
                        pass
                self._more_layout.addRow(QLabel(key), w)
                # store both in _widgets and in a dedicated more-widget mapping
                self._widgets[key] = w
            # NOTE: we intentionally DO NOT add the more details button/widget here
            # so it can be appended to the bottom of the form after other fields have
            # been added. The actual insertion will occur later in the method.

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
                # Exclude known header fields and legacy forcedBatchProcessing and the fields shown separately
                params = {
                    k: v
                    for k, v in props.items()
                    if k
                    not in (
                        "name",
                        "value",
                        "description",
                        "forcedBatchProcessing",
                        "type",
                        "gui_pos",
                        # Exclude the more-details 'computationType' key (renamed from computationalType)
                        "computationType",
                        "batchSize",
                        "id",
                        "inputCount",
                    )
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
                        "type",
                    )

                    if isinstance(v, bool):
                        if readonly:
                            from PyQt6.QtWidgets import QLabel as _QLabel

                            editor = _QLabel(str(v))
                            try:
                                editor.setEnabled(False)
                            except Exception:
                                pass
                        else:
                            from PyQt6.QtWidgets import QCheckBox

                            # Try to reuse an existing checkbox widget to avoid deleting active widgets
                            prev_widget = prev_widgets.get(k)
                            if isinstance(prev_widget, QCheckBox):
                                editor = prev_widget
                                pv = prev_values.get(k)
                                try:
                                    editor.blockSignals(True)
                                    if pv is not None:
                                        editor.setChecked(
                                            str(pv).lower() in ("true", "1", "yes")
                                        )
                                    else:
                                        editor.setChecked(v)
                                except Exception:
                                    editor.setChecked(v)
                                finally:
                                    try:
                                        editor.blockSignals(False)
                                    except Exception:
                                        pass
                            else:
                                editor = QCheckBox()
                                # Preserve previous user input when available
                                pv = prev_values.get(k)
                                try:
                                    if pv is not None:
                                        editor.setChecked(
                                            str(pv).lower() in ("true", "1", "yes")
                                        )
                                    else:
                                        editor.setChecked(v)
                                except Exception:
                                    editor.setChecked(v)
                                # Use singleShot to defer setting parameters to avoid reentrant UI rebuilds
                                editor.stateChanged.connect(
                                    lambda st, name=k: QTimer.singleShot(
                                        0,
                                        lambda st=st, name=name: (
                                            self.vm.set_parameter(name, bool(st))
                                            if hasattr(self.vm, "set_parameter")
                                            else self.vm.set_property(name, bool(st))
                                        ),
                                    )
                                )
                    elif isinstance(v, int):
                        if readonly:
                            from PyQt6.QtWidgets import QLabel as _QLabel

                            editor = _QLabel(str(v))
                            try:
                                editor.setEnabled(False)
                            except Exception:
                                pass
                        else:
                            from PyQt6.QtWidgets import QSpinBox

                            # Reuse an existing QSpinBox where possible to avoid deleting active widgets
                            prev_widget = prev_widgets.get(k)
                            if isinstance(prev_widget, QSpinBox):
                                editor = prev_widget
                                pv = prev_values.get(k)
                                try:
                                    editor.blockSignals(True)
                                    if pv is not None:
                                        editor.setValue(int(pv))
                                    else:
                                        editor.setValue(v)
                                except Exception:
                                    editor.setValue(v)
                                finally:
                                    try:
                                        editor.blockSignals(False)
                                    except Exception:
                                        pass
                            else:
                                editor = QSpinBox()
                                pv = prev_values.get(k)
                                try:
                                    if pv is not None:
                                        editor.setValue(int(pv))
                                    else:
                                        editor.setValue(v)
                                except Exception:
                                    editor.setValue(v)
                                # Defer parameter update to avoid reentrant UI rebuilds while handling widget events
                                editor.valueChanged.connect(
                                    lambda val, name=k: QTimer.singleShot(
                                        0,
                                        lambda val=val, name=name: (
                                            self.vm.set_parameter(name, int(val))
                                            if hasattr(self.vm, "set_parameter")
                                            else self.vm.set_property(name, int(val))
                                        ),
                                    )
                                )
                    elif isinstance(v, float):
                        if readonly:
                            from PyQt6.QtWidgets import QLabel as _QLabel

                            editor = _QLabel(str(v))
                            try:
                                editor.setEnabled(False)
                            except Exception:
                                pass
                        else:
                            from PyQt6.QtWidgets import QDoubleSpinBox

                            # Reuse existing QDoubleSpinBox when safe to avoid deleting active widgets
                            prev_widget = prev_widgets.get(k)
                            if isinstance(prev_widget, QDoubleSpinBox):
                                editor = prev_widget
                                pv = prev_values.get(k)
                                try:
                                    editor.blockSignals(True)
                                    if pv is not None:
                                        editor.setValue(float(pv))
                                    else:
                                        editor.setValue(v)
                                except Exception:
                                    editor.setValue(v)
                                finally:
                                    try:
                                        editor.blockSignals(False)
                                    except Exception:
                                        pass
                            else:
                                editor = QDoubleSpinBox()
                                pv = prev_values.get(k)
                                try:
                                    if pv is not None:
                                        editor.setValue(float(pv))
                                    else:
                                        editor.setValue(v)
                                except Exception:
                                    editor.setValue(v)
                                # Defer parameter update to avoid reentrant UI rebuilds while handling widget events
                                editor.valueChanged.connect(
                                    lambda val, name=k: QTimer.singleShot(
                                        0,
                                        lambda val=val, name=name: (
                                            self.vm.set_parameter(name, float(val))
                                            if hasattr(self.vm, "set_parameter")
                                            else self.vm.set_property(name, float(val))
                                        ),
                                    )
                                )
                    else:
                        # For lists (e.g., inputs), show a comma-separated editable field
                        if isinstance(v, (list, tuple)) and k == "inputs":
                            # Use a scrollable multi-line box for inputs to make it easier to
                            # inspect long lists. Each item shown on its own line.
                            editor = QTextEdit()
                            pv = prev_values.get(k)
                            if pv is not None:
                                editor.setPlainText(pv)
                            else:
                                editor.setPlainText(
                                    "\n".join([str(x) for x in v]) if v else ""
                                )
                            # Make inputs box dynamic like value box
                            from PyQt6.QtWidgets import QSizePolicy

                            expanding_policy = getattr(QSizePolicy, "Expanding", None)
                            if expanding_policy is None and hasattr(
                                QSizePolicy, "Policy"
                            ):
                                try:
                                    expanding_policy = QSizePolicy.Policy.Expanding
                                except Exception:
                                    expanding_policy = 0
                            min_policy = getattr(QSizePolicy, "Minimum", None)
                            if min_policy is None and hasattr(QSizePolicy, "Policy"):
                                try:
                                    min_policy = QSizePolicy.Policy.Minimum
                                except Exception:
                                    min_policy = 0
                            try:
                                editor.setSizePolicy(expanding_policy, min_policy)
                                editor.setMaximumHeight(300)
                                editor.setMinimumHeight(50)
                                try:
                                    self._adjust_textedit_height(editor)
                                except Exception:
                                    pass
                            except Exception:
                                # Widget may have been deleted asynchronously — ignore
                                pass

                            if readonly:
                                editor.setReadOnly(True)
                            else:

                                def _on_inputs_text(name=k, ed=editor):
                                    text = ed.toPlainText()
                                    items = [
                                        t.strip()
                                        for t in text.splitlines()
                                        if t.strip()
                                    ]
                                    try:
                                        if hasattr(self.vm, "set_parameter"):
                                            self.vm.set_parameter(name, items)
                                        else:
                                            self.vm.set_property(name, items)
                                    except Exception:
                                        pass

                                editor.textChanged.connect(_on_inputs_text)
                                try:
                                    editor.textChanged.connect(
                                        lambda ed=editor: self._adjust_textedit_height(
                                            ed
                                        )
                                    )
                                except Exception:
                                    pass
                        else:
                            # For potentially long strings or lists, use QTextEdit (multiline)
                            if (
                                k in ("value", "buffers")
                                or (isinstance(v, str) and len(v) > 120)
                                or (isinstance(v, (list, tuple)) and len(v) > 10)
                            ):
                                editor = QTextEdit()
                                # Represent sequences with one item per line
                                pv = prev_values.get(k)
                                if pv is not None:
                                    editor.setPlainText(pv)
                                else:
                                    if isinstance(v, (list, tuple)):
                                        editor.setPlainText(
                                            "\n".join([str(x) for x in v])
                                        )
                                    else:
                                        editor.setPlainText(str(v))
                                editor.setMinimumHeight(100)
                                if readonly:
                                    editor.setReadOnly(True)
                                else:

                                    def _on_text_changed(name=k, ed=editor):
                                        text = ed.toPlainText()
                                        # Convert back to single string or list where appropriate
                                        if isinstance(v, (list, tuple)):
                                            items = [
                                                t.strip()
                                                for t in text.splitlines()
                                                if t.strip()
                                            ]
                                            try:
                                                if hasattr(self.vm, "set_parameter"):
                                                    self.vm.set_parameter(name, items)
                                                else:
                                                    self.vm.set_property(name, items)
                                            except Exception:
                                                pass
                                        else:
                                            try:
                                                if hasattr(self.vm, "set_parameter"):
                                                    self.vm.set_parameter(name, text)
                                                else:
                                                    self.vm.set_property(name, text)
                                            except Exception:
                                                pass

                                    editor.textChanged.connect(_on_text_changed)
                            else:
                                pv = prev_values.get(k)
                                editor = QLineEdit(pv if pv is not None else str(v))
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

            # Ensure more-details widgets reflect current node properties
            try:
                props = self.vm.get_properties()
                for key in getattr(self, "_more_widgets_keys", []):
                    if key in self._widgets:
                        try:
                            val = props.get(key, "")
                            self._widgets[key].setText(
                                str(val) if val is not None else ""
                            )
                        except Exception:
                            pass
            except Exception:
                pass

            # Add the More details toggle and panel at the BOTTOM of the form
            try:
                # Add after all parameter rows so it appears as the final section
                self.form.addRow(self._more_button)
                self.form.addRow(self._more_widget)
            except Exception:
                pass

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
                    val_w = self._widgets["value"]
                    # QTextEdit uses toPlainText
                    if hasattr(val_w, "toPlainText"):
                        self.vm.set_value(val_w.toPlainText())
                    else:
                        self.vm.set_value(val_w.text())

                # Parameters: read values based on widget type
                for k, w in list(self._widgets.items()):
                    # Skip header and read-only 'more details' fields
                    if k in (
                        "name",
                        "value",
                        "forcedBatch",
                        "Incremental",
                        "type",
                        "gui_pos",
                        "computationalType",
                        "batchSize",
                        "id",
                        "inputCount",
                    ):
                        continue
                    try:
                        if hasattr(w, "isChecked"):
                            self.vm.set_parameter(k, bool(w.isChecked()))
                        elif hasattr(w, "value"):
                            self.vm.set_parameter(k, w.value())
                        elif hasattr(w, "toPlainText"):
                            # QTextEdit
                            text = w.toPlainText()
                            # If originally a list, VM will accept list conversion via set_parameter; best effort
                            if "\n" in text:
                                items = [
                                    t.strip() for t in text.splitlines() if t.strip()
                                ]
                                self.vm.set_parameter(k, items)
                            else:
                                self.vm.set_parameter(k, text)
                        else:
                            self.vm.set_parameter(k, w.text())
                    except Exception:
                        pass

                # Call VM apply
                self.vm.apply_to_node()
            except Exception:
                logging.exception("Error applying node editor changes")
            super().accept()

else:

    class NodeEditorDialog:
        def __init__(self, *args, **kwargs):
            raise ImportError("PyQt6 is required to use NodeEditorDialog")

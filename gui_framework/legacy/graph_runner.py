"""
Graph execution runner with Qt integration.
"""

import threading
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor


class GraphRunner(QObject):
    """Manages graph execution with timer-based stepping."""

    step_completed = pyqtSignal(int)  # Emits current step number
    execution_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    queue_item_started = pyqtSignal(
        object, int
    )  # Emits (graph, iterations) when queue item starts
    queue_item_finished = pyqtSignal(
        object, int
    )  # Emits (graph, iterations) when queue item finishes
    queue_finished = pyqtSignal()  # Emits when entire queue is done

    def __init__(self, parent=None):
        super().__init__(parent)

        self.graph = None
        self.graph_processor = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)

        self.current_step = 0
        self.max_steps = 0
        self.is_running = False
        self.step_interval = 500  # milliseconds
        self.use_multithreading = False  # Default to single thread
        self.processor_type = (
            "concurrent"  # "forward" or "concurrent" - default to concurrent
        )
        self.active_nodes = []  # Track active nodes for forward processing highlighting
        self._exec_thread = None
        self._exec_controller = None

        # Snapshot of initial graph state (iteration 0) for restore functionality
        self._graph_snapshot = None

        # Forward processing sequence (computed by find_execution_sequence)
        self._forward_sequence = None
        self._forward_step_index = 0
        self._forward_sequence_topology_version = None
        self._last_sequence_notice = None

        # === Phase 2: Processing Queue ===
        # Queue of (graph/subgraph, iterations) tuples to execute sequentially
        self._processing_queue = []
        self._queue_running = False
        self._current_queue_index = 0
        # Per-graph snapshots: {graph_id: snapshot_dict}
        self._per_graph_snapshots = {}
        # Repeat mode: restart queue from beginning after completion
        self._queue_repeat = False
        self._queue_repeat_count = 0  # 0 = infinite, N = repeat N times
        self._queue_repeat_current = 0  # Current repeat iteration

    def set_graph(self, graph):
        """Set the graph to execute."""
        # If a background worker exists, stop it to ensure it does not continue
        # processing the old Graph/GraphProcessor instance after we replace the graph.
        try:
            if self._exec_thread is not None and self._exec_thread.is_alive():
                self.stop()
        except Exception:
            pass
        self.graph = graph
        # Create GraphProcessor and inherit verbose setting from the UI (if available)
        self.graph_processor = GraphProcessor(graph=self.graph, verbose=False)
        try:
            parent = self.parent()
            if parent is not None and hasattr(parent, "verbose_check"):
                # If the verbose checkbox exists on the parent window, use its state
                self.graph_processor.verbose = parent.verbose_check.isChecked()
        except Exception:
            # If anything goes wrong reading UI state, leave verbose as created
            pass

        # If using forward or manual processing, reset manual state
        if self.processor_type in ("forward", "manual") and hasattr(
            self.graph_processor, "reset_manual_state"
        ):
            self.graph_processor.reset_manual_state()
            # Mark source nodes as processed for proper initialization
            if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                try:
                    self.graph_processor.mark_source_nodes_as_processed()
                except Exception:
                    pass
            if hasattr(self.graph_processor, "mark_container_nodes_as_processed"):
                try:
                    self.graph_processor.mark_container_nodes_as_processed()
                except Exception:
                    pass

        # Compute forward processing sequence if in forward mode
        if self.processor_type == "forward":
            self._compute_forward_sequence()

        # Capture initial snapshot after graph setup
        # Flush Qt event loop to process any deferred parameter updates (singleShot)
        try:
            import os

            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                try:
                    if not (
                        os.environ.get("CG_PYTEST_RUNNING") == "1"
                        or os.environ.get("PYTEST_RUNNING") == "1"
                    ):
                        app.processEvents()
                except Exception:
                    pass
        except Exception:
            pass
        self.save_graph_snapshot()

        # Clear user_locked_value on all nodes so computation can update values.
        # The snapshot already captured the user-edited values, so they can be
        # restored on reset. But during execution, values must be allowed to change.
        self._unlock_all_node_values()

    def _unlock_all_node_values(self):
        """Clear user_locked_value flag on all nodes to allow computation updates."""
        if not self.graph:
            return
        for node in self.graph.nodes:
            if hasattr(node, "user_locked_value") and node.user_locked_value:
                node.user_locked_value = False

    def _compute_forward_sequence(self):
        """Compute and cache the forward processing execution sequence.

        Uses the sequence finder algorithm to determine the order of node execution
        based on dependencies. The sequence is computed once and reused for each
        iteration through the graph.
        """
        self._forward_sequence = None
        self._forward_step_index = 0
        self._forward_sequence_topology_version = None

        if not self.graph_processor:
            return

        try:
            # Ensure dependency-ready set includes source and container nodes
            # (forward MLP requires initialized ContainerNodes/weights to be ready).
            if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                try:
                    self.graph_processor.mark_source_nodes_as_processed()
                except Exception:
                    pass
            if hasattr(self.graph_processor, "mark_container_nodes_as_processed"):
                try:
                    self.graph_processor.mark_container_nodes_as_processed()
                except Exception:
                    pass

            # Get starting and stopping nodes from the graph
            starting_nodes = getattr(self.graph, "starting_nodes", None)
            stopping_nodes = getattr(self.graph, "stopping_nodes", None)

            # Compute the execution sequence
            result = self.graph_processor.find_execution_sequence(
                starting_nodes=starting_nodes, stopping_nodes=stopping_nodes
            )

            self._forward_sequence = result.get("sequence", [])
            self._forward_sequence_topology_version = getattr(
                self.graph, "topology_version", None
            )

            # Log sequence info for debugging
            if result.get("remaining_non_source_nodes"):
                # Some nodes couldn't be sequenced (possible cycle or disconnection)
                remaining = [n.name for n in result["remaining_non_source_nodes"]]
                print(
                    f"[ForwardProcessing] Warning: {len(remaining)} nodes could not be sequenced: {remaining[:5]}..."
                )

        except Exception as e:
            print(f"[ForwardProcessing] Error computing sequence: {e}")
            self._forward_sequence = []

        # Update UI to display the sequence (if parent main_window is available)
        try:
            main_window = self.parent()
            if main_window and hasattr(main_window, "node_sequence_controller"):
                main_window.node_sequence_controller.display_forward_sequence(
                    self._forward_sequence or []
                )
        except Exception:
            pass  # Silently fail if UI update doesn't work

    def _emit_sequence_note(self, message):
        """Display a lightweight sequence note in status bar and stdout."""
        try:
            if self._last_sequence_notice == message:
                return
            self._last_sequence_notice = message
            parent = self.parent()
            if parent is not None and hasattr(parent, "status_bar"):
                parent.status_bar.showMessage(message, 6000)
        except Exception:
            pass
        try:
            print(f"[Sequence] {message}")
        except Exception:
            pass

    def _refresh_manual_sequence_from_topology(self):
        """Regenerate manual sequence from current topology and assign it to graph."""
        if not self.graph_processor or not self.graph:
            return False
        try:
            self.graph_processor.mark_source_nodes_as_processed()
        except Exception:
            pass
        try:
            self.graph_processor.mark_container_nodes_as_processed()
        except Exception:
            pass

        starting_nodes = getattr(self.graph, "starting_nodes", None)
        stopping_nodes = getattr(self.graph, "stopping_nodes", None)
        result = self.graph_processor.find_execution_sequence(
            starting_nodes=starting_nodes,
            stopping_nodes=stopping_nodes,
            include_remaining_source_nodes=True,
        )
        sequence = result.get("sequence", [])
        starting_set = set(starting_nodes or [])
        filtered_sequence = []
        for step in sequence:
            filtered = [n for n in step if n not in starting_set]
            if filtered:
                filtered_sequence.append(filtered)

        self.graph.set_manual_processing_sequence(filtered_sequence, strict=True)
        return True

    def _ensure_sequences_fresh(self):
        """Ensure forward/manual sequences are in sync with current graph topology."""
        if not self.graph or not self.graph_processor:
            return

        current_topology_version = getattr(self.graph, "topology_version", None)

        if self.processor_type == "forward":
            stale = (
                self._forward_sequence is None
                or self._forward_sequence_topology_version is None
                or (
                    current_topology_version is not None
                    and self._forward_sequence_topology_version
                    != current_topology_version
                )
            )
            if stale:
                self._compute_forward_sequence()
                self._emit_sequence_note(
                    "Forward sequence refreshed automatically after graph topology change."
                )
            return

        if self.processor_type == "manual":
            manual_seq = getattr(self.graph, "manual_processing_sequence", None)
            if not manual_seq:
                return
            seq_version = getattr(self.graph, "manual_sequence_topology_version", None)

            if seq_version is None:
                self._emit_sequence_note(
                    "Manual sequence freshness is unknown (legacy sequence); renew if behavior looks off."
                )
                return

            if (
                current_topology_version is None
                or seq_version == current_topology_version
            ):
                return

            try:
                refreshed = self._refresh_manual_sequence_from_topology()
            except Exception as exc:
                self._emit_sequence_note(
                    f"Manual sequence is stale and auto-refresh failed: {exc}"
                )
                return

            if refreshed:
                self._emit_sequence_note(
                    "Manual sequence was stale and has been regenerated from topology."
                )

    def save_graph_snapshot(self):
        """Capture the current graph state as a snapshot for later restoration.

        This stores node values, buffer contents, DataStream indices, and ContainerNode
        values so the graph can be restored to this state later without affecting
        the iteration counter.
        """
        # Ensure any pending UI-triggered updates run before we capture state
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                try:
                    app.processEvents()
                except Exception:
                    pass
        except Exception:
            pass

        if not self.graph:
            self._graph_snapshot = None
            return

        snapshot = {}

        def save_node_state(node):
            """Save state for a single node (helper for recursion)."""
            node_id = id(node)
            if node_id in snapshot:
                return  # Already saved

            node_state = {"value": None}

            # Store the current value
            if hasattr(node, "value"):
                val = node.value
                # Deep copy lists/arrays to avoid reference issues
                if isinstance(val, list):
                    node_state["value"] = list(val)
                else:
                    node_state["value"] = val

            # Store buffer contents for BufferNodes
            if hasattr(node, "buffer"):
                buf = node.buffer
                if isinstance(buf, list):
                    node_state["buffer"] = list(buf)
                else:
                    node_state["buffer"] = buf
                if hasattr(node, "bufferSize"):
                    node_state["bufferSize"] = node.bufferSize

            # Store DataStreamNode state
            if hasattr(node, "data"):
                data = node.data
                if isinstance(data, list):
                    node_state["data"] = list(data)
                else:
                    node_state["data"] = data
            if hasattr(node, "streamIndex"):
                node_state["streamIndex"] = node.streamIndex

            snapshot[node_id] = node_state

            # Recursively save internal nodes for AbstractNode/CompressedNode
            internal_nodes = getattr(node, "nodes", [])
            if internal_nodes:
                for internal_node in internal_nodes:
                    save_node_state(internal_node)

        for node in self.graph.nodes:
            save_node_state(node)

        self._graph_snapshot = snapshot

    def restore_graph_snapshot(self):
        """Restore the graph to its snapshot state (iteration 0 values).

        This restores node values, buffer contents, and DataStream indices
        WITHOUT changing the current iteration counter.

        Returns:
            True if restoration was successful, False otherwise.
        """
        if not self.graph or not self._graph_snapshot:
            return False

        # Stop any running execution first
        self.stop()

        def restore_node_state(node):
            """Restore state for a single node (helper for recursion)."""
            node_id = id(node)
            if node_id not in self._graph_snapshot:
                # Node was added after snapshot - skip
                return

            node_state = self._graph_snapshot[node_id]

            # Restore value
            if "value" in node_state and hasattr(node, "value"):
                val = node_state["value"]
                if isinstance(val, list):
                    node.value = list(val)
                else:
                    node.value = val

            # Restore buffer for BufferNodes
            if "buffer" in node_state and hasattr(node, "buffer"):
                buf = node_state["buffer"]
                if isinstance(buf, list):
                    node.buffer = list(buf)
                else:
                    node.buffer = buf

            # Restore DataStreamNode state
            if "data" in node_state and hasattr(node, "data"):
                data = node_state["data"]
                if isinstance(data, list):
                    node.data = list(data)
                else:
                    node.data = data
            if "streamIndex" in node_state and hasattr(node, "streamIndex"):
                node.streamIndex = node_state["streamIndex"]

            # Recursively restore internal nodes for AbstractNode/CompressedNode
            internal_nodes = getattr(node, "nodes", [])
            if internal_nodes:
                for internal_node in internal_nodes:
                    restore_node_state(internal_node)

        for node in self.graph.nodes:
            restore_node_state(node)

        # Reset processor state but keep iteration counter
        self._reset_processor_state()

        return True

    def reset_processor(self):
        """Reset only the processor state and iteration counter, preserving node values.

        This resets the iteration counter to 0, clears active nodes, and reinitializes
        the processor state without changing any node values.
        """
        self.stop()
        self.current_step = 0
        self.active_nodes = []

        self._reset_processor_state()

    def _reset_processor_state(self):
        """Internal helper to reset processor state without touching node values or step counter."""
        # Reset forward sequence step index
        self._forward_step_index = 0

        # Reset manual processing state (used by both "forward" and "manual" modes)
        if self.processor_type in ("forward", "manual") and self.graph_processor:
            if hasattr(self.graph_processor, "reset_manual_state"):
                try:
                    self.graph_processor.reset_manual_state()
                except Exception:
                    pass

            # Mark source nodes as processed for proper initialization
            if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                try:
                    self.graph_processor.mark_source_nodes_as_processed()
                except Exception:
                    pass
            if hasattr(self.graph_processor, "mark_container_nodes_as_processed"):
                try:
                    self.graph_processor.mark_container_nodes_as_processed()
                except Exception:
                    pass

        # Recompute forward sequence if in forward mode
        if self.processor_type == "forward":
            self._compute_forward_sequence()

    def start_additional(self, additional_steps):
        """Start execution for a specific number of additional iterations.

        Unlike start(), this method runs exactly `additional_steps` more iterations
        from the current step, properly updating max_steps to reflect the new total.

        Args:
            additional_steps: Number of additional iterations to run.
        """
        if not self.graph:
            self.error_occurred.emit("No graph loaded")
            return
        # Prevent starting multiple concurrent workers
        if self._exec_thread is not None and self._exec_thread.is_alive():
            return

        # Calculate new max_steps as current + additional
        new_max_steps = self.current_step + additional_steps
        self.max_steps = new_max_steps
        self.is_running = True

        # Update adjacency matrix
        try:
            self.graph.UpdateAdjacencyMatrix()
            self._ensure_sequences_fresh()
        except Exception as e:
            self.error_occurred.emit(f"Graph update failed: {str(e)}")
            self.is_running = False
            return

        # Create execution controller
        exec_opts = GraphProcessor.ExecutionOptions(
            step_interval_ms=self.step_interval, allow_pause=True
        )
        controller = GraphProcessor.ExecutionController.from_options(exec_opts)
        self._exec_controller = controller
        self._exec_options = exec_opts

        # Worker runs exactly additional_steps iterations
        def worker():
            try:
                iterations_to_run = additional_steps

                if self.processor_type == "forward":
                    # Use pre-computed sequence from find_execution_sequence
                    if not self._forward_sequence:
                        self._compute_forward_sequence()

                    sequence = self._forward_sequence or []
                    if not sequence:
                        self.error_occurred.emit("No execution sequence computed")
                        return

                    iterations_run = 0
                    while (
                        iterations_run < iterations_to_run
                        and not controller.stop_event.is_set()
                    ):
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        # Get current step in the sequence
                        step_nodes = sequence[self._forward_step_index]

                        # Track for GUI highlighting
                        self.active_nodes = list(step_nodes)
                        self.graph_processor._currently_processing_nodes = list(
                            step_nodes
                        )

                        # Process each node in the current step
                        for node in step_nodes:
                            if not getattr(node, "midCalculation", False):
                                node.UpdateInputs()
                        for node in step_nodes:
                            node.ProcessBatch()

                        # Mark processed
                        self.graph_processor._processed_nodes.update(step_nodes)

                        # Advance step index (cycle back to start after last step)
                        self._forward_step_index = (self._forward_step_index + 1) % len(
                            sequence
                        )

                        iterations_run += 1
                        self.current_step += 1

                        self.step_completed.emit(self.current_step)

                        interval_ms = (
                            getattr(controller, "step_interval_ms", self.step_interval)
                            or 0
                        )
                        if interval_ms:
                            slept = 0
                            while (
                                slept < interval_ms
                                and not controller.stop_event.is_set()
                            ):
                                if controller.pause_event.is_set():
                                    while (
                                        controller.pause_event.is_set()
                                        and not controller.stop_event.is_set()
                                    ):
                                        time.sleep(0.01)
                                    if controller.stop_event.is_set():
                                        break
                                sleep_chunk = min(50, interval_ms - slept) / 1000.0
                                time.sleep(sleep_chunk)
                                slept += sleep_chunk * 1000.0

                elif self.processor_type == "manual":
                    iterations_run = 0
                    while (
                        iterations_run < iterations_to_run
                        and not controller.stop_event.is_set()
                    ):
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        self.graph_processor.ManualProcessing(
                            iterations=1,
                            computation_sequence=getattr(
                                self.graph, "manual_processing_sequence", None
                            ),
                        )
                        iterations_run += 1
                        self.current_step += 1

                        if hasattr(self.graph_processor, "_currently_processing_nodes"):
                            self.active_nodes = list(
                                self.graph_processor._currently_processing_nodes
                            )
                        else:
                            self.active_nodes = []

                        self.step_completed.emit(self.current_step)

                        interval_ms = (
                            getattr(controller, "step_interval_ms", self.step_interval)
                            or 0
                        )
                        if interval_ms:
                            slept = 0
                            while (
                                slept < interval_ms
                                and not controller.stop_event.is_set()
                            ):
                                if controller.pause_event.is_set():
                                    while (
                                        controller.pause_event.is_set()
                                        and not controller.stop_event.is_set()
                                    ):
                                        time.sleep(0.01)
                                    if controller.stop_event.is_set():
                                        break
                                sleep_chunk = min(50, interval_ms - slept) / 1000.0
                                time.sleep(sleep_chunk)
                                slept += sleep_chunk * 1000.0

                else:
                    # Concurrent mode
                    if self.use_multithreading:
                        self.graph_processor.ComputeGraph(
                            iterations_to_run,
                            exec_options=exec_opts,
                            on_iteration_complete=lambda it: self._on_iter_complete(it),
                            controller=controller,
                        )
                    else:
                        self.graph_processor.ComputeGraphSingleThread(
                            iterations_to_run,
                            exec_options=exec_opts,
                            on_iteration_complete=lambda it: self._on_iter_complete(it),
                            controller=controller,
                        )

            except Exception as e:
                self.error_occurred.emit(f"Execution error: {str(e)}")
            finally:
                self.is_running = False
                self.execution_finished.emit()

        self._exec_thread = threading.Thread(target=worker, daemon=True)
        self._exec_thread.start()

    def start(self, max_steps=100, reset_step_counter=True):
        """Start continuous execution.

        Args:
            max_steps: Maximum number of iterations to run.
            reset_step_counter: If True, reset current_step to 0. If False,
                               continue from current step (for resume after completion).
        """
        if not self.graph:
            self.error_occurred.emit("No graph loaded")
            return
        # Prevent starting multiple concurrent workers
        if self._exec_thread is not None and self._exec_thread.is_alive():
            # Already running
            return
        # Prepare for background execution controlled by an execution controller
        self.max_steps = max_steps
        if reset_step_counter:
            self.current_step = 0
        self.is_running = True

        # Update adjacency matrix
        try:
            self.graph.UpdateAdjacencyMatrix()
            self._ensure_sequences_fresh()
        except Exception as e:
            self.error_occurred.emit(f"Graph update failed: {str(e)}")
            self.is_running = False
            return

        # Always take a snapshot at iteration 0 (before first processing)
        # Flush any pending Qt events so deferred parameter updates (singleShot) can apply
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                try:
                    app.processEvents()
                except Exception:
                    pass
        except Exception:
            pass
        # This ensures restore works correctly even if graph was modified after loading
        if self.current_step == 0:
            self.save_graph_snapshot()

        # Create execution controller from GraphProcessor options and keep a reference
        exec_opts = GraphProcessor.ExecutionOptions(
            step_interval_ms=self.step_interval, allow_pause=True
        )
        controller = GraphProcessor.ExecutionController.from_options(exec_opts)
        self._exec_controller = controller
        self._exec_options = exec_opts

        # Worker that runs processor iterations internally
        def worker():
            try:
                if self.processor_type == "forward":
                    # Use pre-computed sequence from find_execution_sequence
                    if not self._forward_sequence:
                        self._compute_forward_sequence()

                    sequence = self._forward_sequence or []
                    if not sequence:
                        self.error_occurred.emit("No execution sequence computed")
                        return

                    iterations_run = 0
                    while (
                        iterations_run < self.max_steps
                        and not controller.stop_event.is_set()
                    ):
                        # Respect pause
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        # Clear processed nodes at the start of each iteration (when cycling back to step 0)
                        if self._forward_step_index == 0 and iterations_run > 0:
                            self.graph_processor._processed_nodes.clear()
                            # Emit signal so GUI can refresh and show all nodes lit
                            self.step_completed.emit(self.current_step)
                            # Small delay to let GUI update before processing starts
                            if self.step_interval > 0:
                                time.sleep(min(50, self.step_interval) / 1000.0)

                        # Get current step in the sequence
                        step_nodes = sequence[self._forward_step_index]

                        # Track for GUI highlighting
                        self.active_nodes = list(step_nodes)
                        self.graph_processor._currently_processing_nodes = list(
                            step_nodes
                        )

                        # Process each node in the current step
                        for node in step_nodes:
                            if not getattr(node, "midCalculation", False):
                                node.UpdateInputs()
                        for node in step_nodes:
                            node.ProcessBatch()

                        # Mark processed
                        self.graph_processor._processed_nodes.update(step_nodes)

                        # Advance step index (cycle back to start after last step)
                        self._forward_step_index = (self._forward_step_index + 1) % len(
                            sequence
                        )

                        iterations_run += 1
                        self.current_step += 1

                        # Emit progress
                        self.step_completed.emit(self.current_step)
                        # Respect step interval (responsive to pause/stop)
                        interval_ms = (
                            getattr(controller, "step_interval_ms", self.step_interval)
                            or 0
                        )
                        if interval_ms:
                            slept = 0
                            # Sleep in small increments so pause/stop remains responsive
                            while (
                                slept < interval_ms
                                and not controller.stop_event.is_set()
                            ):
                                if controller.pause_event.is_set():
                                    # If paused, block here until unpaused or stopped
                                    while (
                                        controller.pause_event.is_set()
                                        and not controller.stop_event.is_set()
                                    ):
                                        time.sleep(0.01)
                                    if controller.stop_event.is_set():
                                        break
                                sleep_chunk = min(50, interval_ms - slept) / 1000.0
                                time.sleep(sleep_chunk)
                                slept += sleep_chunk * 1000.0

                elif self.processor_type == "manual":
                    # Manual processing: call ManualProcessing for one iteration
                    iterations_run = 0
                    while (
                        iterations_run < self.max_steps
                        and not controller.stop_event.is_set()
                    ):
                        # Respect pause
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        # Check if we're at cycle start and clear for visual reset
                        at_cycle_start = (
                            hasattr(self.graph_processor, "_manual_step_index")
                            and self.graph_processor._manual_step_index == 0
                            and iterations_run > 0
                        )

                        if at_cycle_start:
                            # Clear processed nodes for fresh dimming cycle
                            self.graph_processor._processed_nodes.clear()
                            # Emit update so GUI refreshes and shows all nodes lit
                            self.step_completed.emit(self.current_step)
                            # Small delay to let GUI update before processing starts
                            if self.step_interval > 0:
                                time.sleep(min(50, self.step_interval) / 1000.0)

                        # Execute one manual processing iteration (uses graph.manual_processing_sequence)
                        self.graph_processor.ManualProcessing(
                            iterations=1,
                            computation_sequence=getattr(
                                self.graph, "manual_processing_sequence", None
                            ),
                        )
                        iterations_run += 1
                        self.current_step += 1

                        # Update active nodes for highlighting
                        if hasattr(self.graph_processor, "_currently_processing_nodes"):
                            self.active_nodes = list(
                                self.graph_processor._currently_processing_nodes
                            )
                        else:
                            self.active_nodes = []

                        # Emit progress
                        self.step_completed.emit(self.current_step)
                        # Respect step interval
                        interval_ms = (
                            getattr(controller, "step_interval_ms", self.step_interval)
                            or 0
                        )
                        if interval_ms:
                            slept = 0
                            while (
                                slept < interval_ms
                                and not controller.stop_event.is_set()
                            ):
                                if controller.pause_event.is_set():
                                    while (
                                        controller.pause_event.is_set()
                                        and not controller.stop_event.is_set()
                                    ):
                                        time.sleep(0.01)
                                    if controller.stop_event.is_set():
                                        break
                                sleep_chunk = min(50, interval_ms - slept) / 1000.0
                                time.sleep(sleep_chunk)
                                slept += sleep_chunk * 1000.0

                else:
                    # Concurrent mode: let processor run iterations and call back per-iteration
                    if self.use_multithreading:
                        # Pass the actual controller instance so runtime changes affect the running loop
                        self.graph_processor.ComputeGraph(
                            self.max_steps,
                            exec_options=exec_opts,
                            on_iteration_complete=lambda it: self._on_iter_complete(it),
                            controller=controller,
                        )
                    else:
                        self.graph_processor.ComputeGraphSingleThread(
                            self.max_steps,
                            exec_options=exec_opts,
                            on_iteration_complete=lambda it: self._on_iter_complete(it),
                            controller=controller,
                        )

            except Exception as e:
                self.error_occurred.emit(f"Execution error: {str(e)}")
            finally:
                self.is_running = False
                self.execution_finished.emit()

        # Start background worker thread
        self._exec_thread = threading.Thread(target=worker, daemon=True)
        self._exec_thread.start()

    def _on_iter_complete(self, iteration_number: int):
        """Internal callback invoked by GraphProcessor after each iteration."""
        # Increment cumulative step counter and emit progress
        try:
            self.current_step += 1
        except Exception:
            self.current_step = iteration_number

        # Update active nodes (concurrent mode doesn't track active nodes)
        try:
            if self.processor_type == "forward" and hasattr(
                self.graph_processor, "_currently_processing_nodes"
            ):
                self.active_nodes = list(
                    self.graph_processor._currently_processing_nodes
                )
            else:
                self.active_nodes = []
        except Exception:
            self.active_nodes = []

        # Emit progress signal with cumulative step
        try:
            self.step_completed.emit(self.current_step)
        except Exception:
            pass

    def pause(self):
        """Pause execution."""
        # Pause background execution if controller present
        if self._exec_controller is not None:
            try:
                # Use controller API
                if hasattr(self._exec_controller, "pause"):
                    self._exec_controller.pause()
                elif hasattr(self._exec_controller, "pause_event"):
                    self._exec_controller.pause_event.set()
            except Exception:
                pass
        # Stop timer as well
        try:
            self.timer.stop()
        except Exception:
            pass
        self.is_running = False

    def resume(self):
        """Resume execution."""
        # Resume background execution if controller present
        if self._exec_controller is not None:
            try:
                # If the previous controller was stopped (stop_event set) the worker
                # thread was terminated (e.g., during a graph rebuild). In that case,
                # restart execution by starting additional steps equal to remaining
                # iterations. This ensures `resume()` actually restarts processing
                # after a `set_graph()` call.
                if (
                    hasattr(self._exec_controller, "stop_event")
                    and self._exec_controller.stop_event.is_set()
                ):
                    remaining = max(0, self.max_steps - self.current_step)
                    if remaining > 0:
                        try:
                            # Use start_additional to run the remaining iterations
                            self.start_additional(remaining)
                        except Exception:
                            pass
                        return

                # Otherwise just clear pause
                if hasattr(self._exec_controller, "resume"):
                    self._exec_controller.resume()
                elif hasattr(self._exec_controller, "pause_event"):
                    self._exec_controller.pause_event.clear()
            except Exception:
                pass
            self.is_running = True
        else:
            if not self.is_running and self.current_step < self.max_steps:
                self.is_running = True
                try:
                    self.timer.start(self.step_interval)
                except Exception:
                    pass

    def step(self):
        """Execute one step of the graph."""
        if not self.graph or self.current_step >= self.max_steps:
            self.stop()
            return
        # If background execution is running, ignore manual step
        if self._exec_thread is not None and self._exec_thread.is_alive():
            return

        try:
            self._ensure_sequences_fresh()
            if self.processor_type in ("forward", "manual"):
                # Manual/Forward Processing execution
                # Execute one iteration using ManualProcessing
                starting_nodes = None
                if hasattr(self.graph, "starting_nodes") and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes

                self.graph_processor.ManualProcessing(
                    iterations=1,
                    starting_nodes=starting_nodes,
                    computation_sequence=getattr(
                        self.graph, "manual_processing_sequence", None
                    ),
                )

                # Track nodes that were just processed (for highlighting)
                if hasattr(self.graph_processor, "_currently_processing_nodes"):
                    self.active_nodes = list(
                        self.graph_processor._currently_processing_nodes
                    )
                else:
                    self.active_nodes = []
            else:
                # Concurrent processing (traditional)
                self.active_nodes = []  # No active node tracking for concurrent
                # For manual stepping use a short-lived exec options object
                step_opts = GraphProcessor.ExecutionOptions(
                    step_interval_ms=0, allow_pause=False
                )
                if self.use_multithreading:
                    self.graph_processor.ComputeGraph(1, exec_options=step_opts)
                else:
                    self.graph_processor.ComputeGraphSingleThread(
                        1, exec_options=step_opts
                    )

            self.current_step += 1
            self.step_completed.emit(self.current_step)

            if self.current_step >= self.max_steps:
                self.stop()

        except Exception as e:
            self.error_occurred.emit(
                f"Execution error at step {self.current_step}: {str(e)}"
            )
            self.stop()

    def stop(self):
        """Stop execution."""
        # Signal background worker to stop
        if self._exec_controller is not None:
            try:
                # Use controller API
                if hasattr(self._exec_controller, "stop"):
                    self._exec_controller.stop()
                elif hasattr(self._exec_controller, "stop_event"):
                    self._exec_controller.stop_event.set()
            except Exception:
                pass

        # Stop timer (if used)
        try:
            self.timer.stop()
        except Exception:
            pass

        # Join thread if present
        if self._exec_thread is not None:
            try:
                self._exec_thread.join(timeout=1.0)
            except Exception:
                pass
            self._exec_thread = None
            self._exec_controller = None
            self._exec_options = None

        self.is_running = False
        self.execution_finished.emit()

    def reset(self):
        """Full reset: restore graph to snapshot state AND reset processor/iteration counter.

        This combines restore_graph_snapshot() and reset_processor() for a complete reset
        to iteration 0 state.
        """
        self.stop()
        self.current_step = 0
        self.active_nodes = []

        # If we have a snapshot, restore from it; otherwise reset nodes individually
        if self._graph_snapshot:
            self.restore_graph_snapshot()
        else:
            # Fallback: Reset all nodes individually
            if self.graph:
                import logging
                import traceback

                logging.getLogger(__name__).debug(
                    "GraphRunner.reset called (no snapshot)\n%s",
                    "\n".join(traceback.format_stack()),
                )
                reset_count = 0
                for node in self.graph.nodes:
                    try:
                        if hasattr(node, "ResetValue"):
                            logging.getLogger(__name__).debug(
                                "Resetting node %s (user_locked=%s)",
                                getattr(node, "name", str(node)),
                                getattr(node, "user_locked_value", False),
                            )
                            node.ResetValue()
                            reset_count += 1
                    except Exception:
                        logging.getLogger(__name__).exception(
                            "Error resetting node %s", getattr(node, "name", str(node))
                        )
                logging.getLogger(__name__).debug(
                    "GraphRunner.reset: reset %s nodes", reset_count
                )

        # Reset processor state
        self._reset_processor_state()

    def set_speed(self, interval_ms):
        """Set the step interval in milliseconds."""
        # Allow 0ms for maximum speed (Qt timer accepts 0 to fire as fast as possible)
        self.step_interval = max(0, interval_ms)
        # Update any running Qt timer
        if self.timer.isActive():
            try:
                self.timer.setInterval(self.step_interval)
            except Exception:
                pass

        # Propagate to stored exec options and controller if present
        try:
            if hasattr(self, "_exec_options") and self._exec_options is not None:
                try:
                    self._exec_options.step_interval_ms = self.step_interval
                except Exception:
                    pass

            if self._exec_controller is not None:
                # Prefer controller API attribute if available
                if hasattr(self._exec_controller, "step_interval_ms"):
                    try:
                        self._exec_controller.step_interval_ms = self.step_interval
                    except Exception:
                        pass
        except Exception:
            pass

    def set_threading_mode(self, use_multithreading):
        """Set whether to use multithreading for graph execution.

        Args:
            use_multithreading: True for multi-threaded, False for single-threaded
        """
        self.use_multithreading = use_multithreading

    def set_processor_type(self, processor_type):
        """Set the processor type for graph execution.

        Args:
            processor_type: "forward" or "manual" for ManualProcessing,
                          "concurrent" for traditional concurrent processing
        """
        self.processor_type = processor_type

        # Reset forward sequence state
        self._forward_sequence = None
        self._forward_step_index = 0

        # Reset manual state when switching to forward or manual processing
        if processor_type in ("forward", "manual") and self.graph_processor:
            if hasattr(self.graph_processor, "reset_manual_state"):
                try:
                    self.graph_processor.reset_manual_state()
                except Exception:
                    pass

            # Mark source nodes as processed for initialization
            if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                try:
                    self.graph_processor.mark_source_nodes_as_processed()
                except Exception:
                    pass
            if hasattr(self.graph_processor, "mark_container_nodes_as_processed"):
                try:
                    self.graph_processor.mark_container_nodes_as_processed()
                except Exception:
                    pass

        # Compute forward sequence if switching to forward mode
        if processor_type == "forward" and self.graph_processor:
            self._compute_forward_sequence()

    # === Phase 2: Processing Queue Methods ===

    def add_to_queue(self, graph, iterations):
        """Add a graph/subgraph to the processing queue.

        Args:
            graph: The Graph or sub-graph to process
            iterations: Number of iterations to run for this graph
        """
        self._processing_queue.append((graph, iterations))

    def clear_queue(self):
        """Clear the processing queue."""
        self._processing_queue = []
        self._current_queue_index = 0

    def get_queue(self):
        """Get the current processing queue.

        Returns:
            List of (graph, iterations) tuples
        """
        return list(self._processing_queue)

    def set_queue_repeat(self, repeat: bool, count: int = 0):
        """Set whether the queue should repeat after completion.

        Args:
            repeat: True to enable repeat mode
            count: Number of times to repeat (0 = infinite)
        """
        self._queue_repeat = repeat
        self._queue_repeat_count = count
        self._queue_repeat_current = 0

    def is_queue_repeat(self) -> bool:
        """Check if queue repeat mode is enabled."""
        return self._queue_repeat

    def get_queue_repeat_count(self) -> int:
        """Get the queue repeat count (0 = infinite)."""
        return self._queue_repeat_count

    def remove_from_queue(self, index):
        """Remove an item from the queue by index.

        Args:
            index: The index of the item to remove
        """
        if 0 <= index < len(self._processing_queue):
            self._processing_queue.pop(index)

    def start_queue(self):
        """Start processing the queue sequentially.

        Each queue item runs for its specified iterations, then the next item starts.
        """
        if not self._processing_queue:
            self.error_occurred.emit("Processing queue is empty")
            return

        if self._queue_running:
            return  # Already running

        self._queue_running = True
        self._queue_repeat_current = 0  # Reset repeat counter
        self._current_queue_index = 0
        self._run_next_queue_item()

    def _run_next_queue_item(self):
        """Internal: Run the next item in the queue."""
        if self._current_queue_index >= len(self._processing_queue):
            # Queue finished - check if we should repeat
            if self._queue_repeat and self._processing_queue:
                self._queue_repeat_current += 1
                # Check if we've reached the repeat limit (0 = infinite)
                if (
                    self._queue_repeat_count == 0
                    or self._queue_repeat_current < self._queue_repeat_count
                ):
                    self._current_queue_index = 0
                    self._run_next_queue_item()
                    return
            self._queue_running = False
            self.queue_finished.emit()
            return

        graph, iterations = self._processing_queue[self._current_queue_index]

        # Set up for this graph
        self.set_processing_subgraph(graph if graph != self.graph else None)

        # Emit signal that we're starting this queue item
        self.queue_item_started.emit(graph, iterations)

        # Connect to execution_finished to chain to next item
        # Disconnect any previous connection first
        try:
            self.execution_finished.disconnect(self._on_queue_item_finished)
        except Exception:
            pass
        self.execution_finished.connect(self._on_queue_item_finished)

        # Start execution for this graph
        self.start(max_steps=iterations, reset_step_counter=True)

    def _on_queue_item_finished(self):
        """Internal: Called when a queue item finishes."""
        if not self._queue_running:
            return

        # Disconnect to avoid multiple calls
        try:
            self.execution_finished.disconnect(self._on_queue_item_finished)
        except Exception:
            pass

        # Emit signal that this item finished
        if self._current_queue_index < len(self._processing_queue):
            graph, iterations = self._processing_queue[self._current_queue_index]
            self.queue_item_finished.emit(graph, iterations)

        # Move to next item
        self._current_queue_index += 1
        self._run_next_queue_item()

    def stop_queue(self):
        """Stop the queue processing."""
        self._queue_running = False
        try:
            self.execution_finished.disconnect(self._on_queue_item_finished)
        except Exception:
            pass
        self.stop()

    def is_queue_running(self):
        """Check if queue is currently running."""
        return self._queue_running

    # === Phase 2: Per-Graph Reset/Restore ===

    def save_graph_snapshot_for(self, graph):
        """Save a snapshot for a specific graph/subgraph.

        Args:
            graph: The graph to snapshot
        """
        if not graph:
            return

        graph_id = getattr(graph, "graph_id", id(graph))
        snapshot = {}

        def save_node_state(node):
            node_id = id(node)
            if node_id in snapshot:
                return

            node_state = {"value": None}

            if hasattr(node, "value"):
                val = node.value
                if isinstance(val, list):
                    node_state["value"] = list(val)
                else:
                    node_state["value"] = val

            if hasattr(node, "buffer"):
                buf = node.buffer
                if isinstance(buf, list):
                    node_state["buffer"] = list(buf)
                else:
                    node_state["buffer"] = buf

            if hasattr(node, "data"):
                data = node.data
                if isinstance(data, list):
                    node_state["data"] = list(data)
                else:
                    node_state["data"] = data

            if hasattr(node, "streamIndex"):
                node_state["streamIndex"] = node.streamIndex

            snapshot[node_id] = node_state

            internal_nodes = getattr(node, "nodes", [])
            if internal_nodes:
                for internal_node in internal_nodes:
                    save_node_state(internal_node)

        for node in graph.nodes:
            save_node_state(node)

        self._per_graph_snapshots[graph_id] = snapshot

    def restore_graph_snapshot_for(self, graph):
        """Restore a specific graph/subgraph to its snapshot state.

        Args:
            graph: The graph to restore

        Returns:
            True if restored, False if no snapshot found
        """
        if not graph:
            return False

        graph_id = getattr(graph, "graph_id", id(graph))
        snapshot = self._per_graph_snapshots.get(graph_id)

        if not snapshot:
            return False

        def restore_node_state(node):
            node_id = id(node)
            if node_id not in snapshot:
                return

            node_state = snapshot[node_id]

            if "value" in node_state and hasattr(node, "value"):
                val = node_state["value"]
                if isinstance(val, list):
                    node.value = list(val)
                else:
                    node.value = val

            if "buffer" in node_state and hasattr(node, "buffer"):
                buf = node_state["buffer"]
                if isinstance(buf, list):
                    node.buffer = list(buf)
                else:
                    node.buffer = buf

            if "data" in node_state and hasattr(node, "data"):
                data = node_state["data"]
                if isinstance(data, list):
                    node.data = list(data)
                else:
                    node.data = data

            if "streamIndex" in node_state and hasattr(node, "streamIndex"):
                node.streamIndex = node_state["streamIndex"]

            internal_nodes = getattr(node, "nodes", [])
            if internal_nodes:
                for internal_node in internal_nodes:
                    restore_node_state(internal_node)

        for node in graph.nodes:
            restore_node_state(node)

        return True

    def reset_graph(self, graph):
        """Reset a specific graph/subgraph - restore values and reset processor state.

        Args:
            graph: The graph to reset
        """
        if not graph:
            return

        # Try to restore from snapshot first
        if not self.restore_graph_snapshot_for(graph):
            # Fallback: Reset nodes individually
            for node in graph.nodes:
                if hasattr(node, "ResetValue"):
                    node.ResetValue()

        # If this is the currently processing graph, reset processor state too
        if graph == self.get_processing_graph():
            self._reset_processor_state()

    def set_processing_subgraph(self, subgraph):
        """Set a specific subgraph to process instead of the full graph.

        Args:
            subgraph: A Graph object representing the subgraph to process,
                      or None to process the full mother graph.
        """
        self._processing_subgraph = subgraph

        # If a subgraph is selected, create a new processor for it
        if subgraph is not None and subgraph != self.graph:
            self.graph_processor = GraphProcessor(graph=subgraph, verbose=False)
            try:
                parent = self.parent()
                if parent is not None and hasattr(parent, "verbose_check"):
                    self.graph_processor.verbose = parent.verbose_check.isChecked()
            except Exception:
                pass
        elif self.graph is not None:
            # Reset to mother graph
            self.graph_processor = GraphProcessor(graph=self.graph, verbose=False)
            try:
                parent = self.parent()
                if parent is not None and hasattr(parent, "verbose_check"):
                    self.graph_processor.verbose = parent.verbose_check.isChecked()
            except Exception:
                pass

    def get_processing_graph(self):
        """Get the graph currently being processed (subgraph or mother graph)."""
        subgraph = getattr(self, "_processing_subgraph", None)
        if subgraph is not None:
            return subgraph
        return self.graph

    def single_step(self):
        """Execute a single step without timer."""
        if not self.is_running:
            self.step()

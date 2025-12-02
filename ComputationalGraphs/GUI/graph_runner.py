"""
Graph execution runner with Qt integration.
"""

import threading
import time

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor


class GraphRunner(QObject):
    """Manages graph execution with timer-based stepping."""

    step_completed = pyqtSignal(int)  # Emits current step number
    execution_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

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

    def set_graph(self, graph):
        """Set the graph to execute."""
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

        # If using forward processing, reset state to ensure fresh initialization
        if self.processor_type == "forward" and hasattr(
            self.graph_processor, "reset_forward_state"
        ):
            self.graph_processor.reset_forward_state()
        # If using manual processing, reset manual state to ensure index starts at 0
        if self.processor_type == "manual" and hasattr(
            self.graph_processor, "reset_manual_state"
        ):
            self.graph_processor.reset_manual_state()

        # If using forward processing, prefer graph-level preparation:
        # Many forward-processing graphs (e.g., MLPGraphForwardProcessing) implement
        # `PrepareForForwardProcessing(processor)` which marks source and container
        # nodes as processed for the first forward pass. Call that if available.
        if self.processor_type == "forward":
            if hasattr(self.graph, "PrepareForForwardProcessing"):
                try:
                    # Let the graph prepare itself using the processor instance
                    self.graph.PrepareForForwardProcessing(self.graph_processor)
                except Exception:
                    # Fall back to any processor helper if graph-level prep fails
                    if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                        try:
                            self.graph_processor.mark_source_nodes_as_processed()
                        except Exception:
                            pass
            else:
                # If graph does not provide PrepareForForwardProcessing, attempt processor helper
                if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                    try:
                        self.graph_processor.mark_source_nodes_as_processed()
                    except Exception:
                        pass
            # Do NOT automatically mark ContainerNodes as processed here.
            # Marking container (weight) nodes should be handled explicitly
            # by graph builders or user actions so they can participate in
            # forward-processing cycles and updates correctly.

        # Capture initial snapshot after graph setup
        self.save_graph_snapshot()

    def save_graph_snapshot(self):
        """Capture the current graph state as a snapshot for later restoration.

        This stores node values, buffer contents, DataStream indices, and ContainerNode
        values so the graph can be restored to this state later without affecting
        the iteration counter.
        """
        if not self.graph:
            self._graph_snapshot = None
            return

        snapshot = {}
        for node in self.graph.nodes:
            node_id = id(node)
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

        for node in self.graph.nodes:
            node_id = id(node)
            if node_id not in self._graph_snapshot:
                # Node was added after snapshot - skip
                continue

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
        # Reset forward processing state
        if self.processor_type == "forward" and self.graph_processor:
            if hasattr(self.graph_processor, "reset_forward_state"):
                self.graph_processor.reset_forward_state()

            # Re-prepare the graph for forward processing
            if hasattr(self.graph, "PrepareForForwardProcessing"):
                try:
                    self.graph.PrepareForForwardProcessing(self.graph_processor)
                except Exception:
                    if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                        try:
                            self.graph_processor.mark_source_nodes_as_processed()
                        except Exception:
                            pass
                    if hasattr(
                        self.graph_processor, "mark_container_nodes_as_processed"
                    ):
                        try:
                            self.graph_processor.mark_container_nodes_as_processed()
                        except Exception:
                            pass
            else:
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

        # Reset manual processing state
        if self.processor_type == "manual" and self.graph_processor:
            if hasattr(self.graph_processor, "reset_manual_state"):
                try:
                    self.graph_processor.reset_manual_state()
                except Exception:
                    pass

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
                    starting_nodes = None
                    if (
                        hasattr(self.graph, "starting_nodes")
                        and self.graph.starting_nodes
                    ):
                        starting_nodes = self.graph.starting_nodes

                    iterations_run = 0
                    while (
                        iterations_run < iterations_to_run
                        and not controller.stop_event.is_set()
                    ):
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        self.graph_processor.ForwardProcessing(
                            iterations=1, starting_nodes=starting_nodes
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
        except Exception as e:
            self.error_occurred.emit(f"Graph update failed: {str(e)}")
            self.is_running = False
            return

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
                    starting_nodes = None
                    if (
                        hasattr(self.graph, "starting_nodes")
                        and self.graph.starting_nodes
                    ):
                        starting_nodes = self.graph.starting_nodes

                    iterations_run = 0
                    while (
                        iterations_run < self.max_steps
                        and not controller.stop_event.is_set()
                    ):
                        # Respect pause
                        while controller.pause_event.is_set():
                            time.sleep(0.01)

                        # Run a single forward iteration
                        self.graph_processor.ForwardProcessing(
                            iterations=1, starting_nodes=starting_nodes
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
                # Use controller API
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
            if self.processor_type == "forward":
                # Forward Processing execution
                # Execute one iteration
                # Explicitly pass starting_nodes to ensure correct initialization
                starting_nodes = None
                if hasattr(self.graph, "starting_nodes") and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes

                self.graph_processor.ForwardProcessing(
                    iterations=1, starting_nodes=starting_nodes
                )

                # Track nodes that were just processed (for highlighting)
                if hasattr(self.graph_processor, "_currently_processing_nodes"):
                    self.active_nodes = list(
                        self.graph_processor._currently_processing_nodes
                    )
                else:
                    self.active_nodes = []

                # Note: We don't stop when active_remaining == 0 because the graph
                # may reactivate nodes in subsequent iterations (e.g., DataStreamNodes cycling)
            elif self.processor_type == "manual":
                # Single-step manual processing uses graph.manual_processing_sequence
                self.graph_processor.ManualProcessing(
                    iterations=1,
                    computation_sequence=getattr(
                        self.graph, "manual_processing_sequence", None
                    ),
                )
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
                for node in self.graph.nodes:
                    if hasattr(node, "ResetValue"):
                        node.ResetValue()

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
            processor_type: "forward" for Forward Processing (autonomous execution),
                          "concurrent" for traditional concurrent processing
        """
        self.processor_type = processor_type

        # Reset forward state when switching to Forward Processing
        if processor_type == "forward" and self.graph_processor:
            if hasattr(self.graph_processor, "reset_forward_state"):
                self.graph_processor.reset_forward_state()

            # Prefer graph-level preparation which may mark both sources and
            # container (weight) nodes appropriately. Fall back to processor
            # helpers if graph-level method is not available.
            if hasattr(self.graph, "PrepareForForwardProcessing"):
                try:
                    self.graph.PrepareForForwardProcessing(self.graph_processor)
                except Exception:
                    # Fallback to processor helpers
                    if hasattr(self.graph_processor, "mark_source_nodes_as_processed"):
                        try:
                            self.graph_processor.mark_source_nodes_as_processed()
                        except Exception:
                            pass
                    if hasattr(
                        self.graph_processor, "mark_container_nodes_as_processed"
                    ):
                        try:
                            self.graph_processor.mark_container_nodes_as_processed()
                        except Exception:
                            pass
            else:
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
            # Do NOT automatically mark ContainerNodes as processed here.
            # Marking container (weight) nodes should be handled explicitly
            # by graph builders or user actions so they can participate in
            # forward-processing cycles and updates correctly.
            if (
                processor_type == "manual"
                and self.graph_processor
                and hasattr(self.graph_processor, "reset_manual_state")
            ):
                try:
                    self.graph_processor.reset_manual_state()
                except Exception:
                    pass

    def single_step(self):
        """Execute a single step without timer."""
        if not self.is_running:
            self.step()

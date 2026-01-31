import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional


class GraphProcessor:
    """Clean GraphProcessor implementation with controller support."""

    def __init__(
        self,
        graph,
        max_workers=None,
        verbose=True,
        visual=False,
        auto_threading=True,
        chunk_size=None,
    ):
        self.graph = graph
        self.time = 0
        self.verbose = verbose
        self.visual = visual

        num_nodes = len(graph.nodes)
        if max_workers is None:
            self.max_workers = (
                1 if num_nodes < 1000 else max(1, (os.cpu_count() or 4) // 2)
            )
            self._auto_workers = True
        else:
            self.max_workers = max_workers
            self._auto_workers = False

        # Backwards compatibility helper - some tests/legacy code check this attribute.
        # Keep in sync with the inferred single-thread decision above.
        self.use_single_thread_mode = self.max_workers <= 1

        if chunk_size is None:
            self.chunk_size = max(
                1, num_nodes // (self.max_workers * 4) if num_nodes >= 4 else 1
            )
        else:
            self.chunk_size = chunk_size

        # State for manual processing
        self._manual_step_index = 0  # Current position in processing sequence
        self._currently_processing_nodes = []  # For GUI highlighting
        self._processed_nodes = set()  # Nodes processed in current cycle

    def _chunk_nodes(self, nodes):
        for i in range(0, len(nodes), self.chunk_size):
            yield nodes[i : i + self.chunk_size]

    def _process_node_chunk(self, nodes, method_name):
        for node in nodes:
            getattr(node, method_name)()

    @dataclass
    class ExecutionOptions:
        """Single argument to configure execution behaviour.

        Use this instead of constructing controller objects manually. Example:
            opts = GraphProcessor.ExecutionOptions(step_interval_ms=100)
            proc.ComputeGraph(10, exec_options=opts)
        """

        step_interval_ms: int = 0
        allow_pause: bool = True

    class ExecutionController:
        """Internal execution controller.

        Exposes a small API (`pause()`, `resume()`, `stop()`) and has
        threading.Event attributes `pause_event` and `stop_event`.
        """

        def __init__(self, step_interval_ms: int = 0, allow_pause: bool = True):
            self.pause_event = threading.Event()
            self.stop_event = threading.Event()
            self.step_interval_ms = step_interval_ms
            self.allow_pause = allow_pause

        def pause(self):
            if self.allow_pause:
                self.pause_event.set()

        def resume(self):
            self.pause_event.clear()

        def stop(self):
            self.stop_event.set()

        @staticmethod
        def from_options(opts: Optional["GraphProcessor.ExecutionOptions"]):
            if opts is None:
                return GraphProcessor.ExecutionController()
            return GraphProcessor.ExecutionController(
                step_interval_ms=opts.step_interval_ms, allow_pause=opts.allow_pause
            )

    def ComputeGraph(
        self,
        iterations=1,
        exec_options: Optional[ExecutionOptions] = None,
        on_iteration_complete=None,
        controller: Optional["GraphProcessor.ExecutionController"] = None,
    ):
        """Run concurrent ComputeGraph for `iterations`.

        Parameters:
        - `exec_options`: (preferred) an instance of `ExecutionOptions` to configure speed/pause behaviour.
        - `controller`: (deprecated) pre-existing controller-like object providing `stop_event`, `pause_event`, and `step_interval_ms`.
        - `on_iteration_complete`: optional callback called after each iteration with the iteration index (1-based).
        """
        # Use provided controller if given, otherwise build one from exec_options
        controller_obj = (
            controller
            if controller is not None
            else GraphProcessor.ExecutionController.from_options(exec_options)
        )

        if self.max_workers <= 1:
            return self.ComputeGraphSingleThread(
                iterations,
                exec_options=exec_options,
                on_iteration_complete=on_iteration_complete,
                controller=controller_obj,
            )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for t in range(iterations):
                # controller stop
                if (
                    getattr(controller_obj, "stop_event", None) is not None
                    and controller_obj.stop_event.is_set()
                ):
                    break
                # controller pause (cooperative)
                if getattr(controller_obj, "pause_event", None) is not None:
                    while controller_obj.pause_event.is_set():
                        time.sleep(0.01)

                # Phase 1: UpdateInputs for nodes that need it.
                # Collect futures and wait for completion to avoid races where
                # ProcessBatch reads inputs while UpdateInputs is still running.
                nodes_to_update = [
                    n
                    for n in self.graph.nodes
                    if not getattr(n, "midCalculation", False)
                ]
                update_futures = []
                for chunk in self._chunk_nodes(nodes_to_update):
                    update_futures.append(
                        executor.submit(self._process_node_chunk, chunk, "UpdateInputs")
                    )
                # Wait for all UpdateInputs tasks to finish before proceeding.
                for uf in update_futures:
                    uf.result()

                # Phase 2: ProcessBatch for all nodes. Wait for completion.
                futures = []
                for chunk in self._chunk_nodes(self.graph.nodes):
                    futures.append(
                        executor.submit(self._process_node_chunk, chunk, "ProcessBatch")
                    )
                for f in futures:
                    f.result()

                self.time += 1
                if on_iteration_complete:
                    try:
                        on_iteration_complete(t + 1)
                    except Exception:
                        pass

                interval = getattr(controller_obj, "step_interval_ms", None)
                if interval:
                    time.sleep(interval / 1000.0)

        return

    def ComputeGraphSingleThread(
        self,
        iterations=1,
        exec_options: Optional[ExecutionOptions] = None,
        on_iteration_complete=None,
        controller: Optional["GraphProcessor.ExecutionController"] = None,
    ):
        # Use provided controller if given, otherwise build one from exec_options
        controller_obj = (
            controller
            if controller is not None
            else GraphProcessor.ExecutionController.from_options(exec_options)
        )

        for t in range(iterations):
            if (
                getattr(controller_obj, "stop_event", None) is not None
                and controller_obj.stop_event.is_set()
            ):
                break
            if getattr(controller_obj, "pause_event", None) is not None:
                while controller_obj.pause_event.is_set():
                    time.sleep(0.01)

            for node in self.graph.nodes:
                if not getattr(node, "midCalculation", False):
                    node.UpdateInputs()
            for node in self.graph.nodes:
                node.ProcessBatch()

            self.time += 1
            if on_iteration_complete:
                try:
                    on_iteration_complete(t + 1)
                except Exception:
                    pass

            interval = getattr(controller_obj, "step_interval_ms", None)
            if interval:
                time.sleep(interval / 1000.0)

        return

    def __repr__(self):
        return f"GraphProcessor with {len(self.graph.nodes)} nodes at time={self.time}."

    # =========================================================================
    # Manual Processing
    # =========================================================================

    def reset_manual_state(self):
        """Reset manual processing state for a fresh execution run."""
        self._manual_step_index = 0
        self._currently_processing_nodes = []
        self._processed_nodes = set()

    def mark_source_nodes_as_processed(self):
        """Mark nodes with no predecessors as processed.

        Returns the count of nodes marked.
        """
        count = 0
        for node in self.graph.nodes:
            if len(node.predecessors) == 0:
                self._processed_nodes.add(node)
                count += 1
        return count

    def mark_container_nodes_as_processed(self):
        """Mark ContainerNodes as processed (useful when backprop is attached).

        Returns the count of nodes marked.
        """
        from ComputationalGraphs.Nodes.ContainerNode import ContainerNode

        count = 0
        for node in self.graph.nodes:
            if isinstance(node, ContainerNode):
                self._processed_nodes.add(node)
                count += 1
        return count

    def ManualProcessing(
        self,
        iterations=1,
        computation_sequence=None,
        starting_nodes=None,
        exec_options: Optional[ExecutionOptions] = None,
        on_iteration_complete=None,
        controller: Optional["GraphProcessor.ExecutionController"] = None,
    ):
        """Execute nodes in a user-defined sequence.

        Processing loops: starting_nodes -> seq[0] -> ... -> seq[n] -> repeat
        until all iterations are exhausted.

        Parameters:
        - iterations: Total iterations (each processes one step in cycle).
        - computation_sequence: List of node sets to process in order.
            Defaults to graph.manual_processing_sequence.
        - starting_nodes: Nodes to process at the start of each cycle.
            Defaults to graph.starting_nodes.
        - exec_options: ExecutionOptions for pause/step control.
        - on_iteration_complete: Callback after each iteration (1-based).
        - controller: Pre-existing ExecutionController (deprecated).
        """
        # Use graph attributes as defaults
        if computation_sequence is None:
            computation_sequence = getattr(
                self.graph, "manual_processing_sequence", None
            )
        if starting_nodes is None:
            starting_nodes = getattr(self.graph, "starting_nodes", [])

        # Build full cycle: starting_nodes first, then each step in sequence
        if computation_sequence is not None and len(computation_sequence) > 0:
            full_sequence = [list(starting_nodes)] + [
                list(step) for step in computation_sequence
            ]
        else:
            # No sequence defined - just process starting_nodes repeatedly
            full_sequence = [list(starting_nodes)] if starting_nodes else []

        if not full_sequence:
            # Nothing to process
            return

        controller_obj = (
            controller
            if controller is not None
            else GraphProcessor.ExecutionController.from_options(exec_options)
        )

        for t in range(iterations):
            # Check stop signal
            if (
                getattr(controller_obj, "stop_event", None) is not None
                and controller_obj.stop_event.is_set()
            ):
                break

            # Check pause signal
            if getattr(controller_obj, "pause_event", None) is not None:
                while controller_obj.pause_event.is_set():
                    time.sleep(0.01)

            # Get current step in the cycle
            step_nodes = full_sequence[self._manual_step_index]

            # Track for GUI highlighting
            self._currently_processing_nodes = list(step_nodes)

            # Phase 1: UpdateInputs for nodes that need it
            for node in step_nodes:
                if not getattr(node, "midCalculation", False):
                    node.UpdateInputs()

            # Phase 2: ProcessBatch
            for node in step_nodes:
                node.ProcessBatch()

            # Mark these nodes as processed
            self._processed_nodes.update(step_nodes)

            # Advance step index (cycle back to start after last step)
            self._manual_step_index = (self._manual_step_index + 1) % len(full_sequence)

            self.time += 1

            if on_iteration_complete:
                try:
                    on_iteration_complete(t + 1)
                except Exception:
                    pass

            # Step interval for visualization
            interval = getattr(controller_obj, "step_interval_ms", None)
            if interval:
                time.sleep(interval / 1000.0)

        # Note: Do NOT clear _currently_processing_nodes here.
        # The GUI needs to read it after ManualProcessing returns to highlight active nodes.

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Optional


class GraphProcessor:
    """Clean GraphProcessor implementation with controller support."""

    _DEFAULT_SEQUENCE_PREFIX_PRIORITY = [
        "Mul_x",
        "Add_L",
        "Act_L",
        "Mul_H",
        "D_H",
        "Add_y",
        "y",
        "Error_",
        "D_y",
        "EG_y",
        "LRMult_y",
        "WG_",
        "dW_H",
        "WGS_",
        "EG_H",
        "W_H",
        "LRMult_H",
        "dW_x",
        "W_x",
        "x",
        "L_",
    ]

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

    @classmethod
    def _default_sequence_sort_key(cls, node):
        node_name = getattr(node, "name", "") or ""
        for idx, prefix in enumerate(cls._DEFAULT_SEQUENCE_PREFIX_PRIORITY):
            if node_name.startswith(prefix):
                return (idx, node_name)
        return (len(cls._DEFAULT_SEQUENCE_PREFIX_PRIORITY), node_name)

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
                        if getattr(controller_obj, "stop_event", None) is not None and controller_obj.stop_event.is_set():
                            break
                        time.sleep(0.01)

                if (
                    getattr(controller_obj, "stop_event", None) is not None
                    and controller_obj.stop_event.is_set()
                ):
                    break

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
                    if getattr(controller_obj, "stop_event", None) is not None and controller_obj.stop_event.is_set():
                        break
                    time.sleep(0.01)

            if getattr(controller_obj, "stop_event", None) is not None and controller_obj.stop_event.is_set():
                break

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
        from zorvan.Nodes.ContainerNode import ContainerNode

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

            # Clear processed nodes when starting a new cycle
            if self._manual_step_index == 0:
                self._processed_nodes.clear()

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

    # =========================================================================
    # Sequence Finder for Forward Processing
    # =========================================================================

    def find_execution_sequence(
        self,
        starting_nodes=None,
        stopping_nodes=None,
        node_sort_key=None,
        include_remaining_source_nodes=False,
    ):
        """
        Compute the execution sequence for forward processing based on node dependencies.

        Algorithm:
          1. Start with any pre-marked processed nodes (`self._processed_nodes`) plus
              starting_nodes as the first executable step
        2. At each step, flag successors of current nodes as candidates
        3. Candidates whose ALL predecessors are in the processed set get added to the next step
        4. Repeat until no more nodes can be added
        5. If unadded nodes remain and they are all source nodes (no predecessors),
           stop and return the sequence (source nodes not in starting_nodes are skipped)
        6. If unadded non-source nodes remain, they are unreachable (cycle or disconnected)

        Parameters:
        - starting_nodes: List of nodes to start execution from.
            Defaults to graph.starting_nodes.
        - stopping_nodes: List of nodes that should not trigger successor activation.
            Defaults to graph.stopping_nodes if it exists.
        - node_sort_key: Optional callable to deterministically sort nodes within
            each step. Defaults to a built-in neural-network-friendly ordering key.
        - include_remaining_source_nodes: If True, append remaining unsequenced
            source nodes (nodes with no predecessors) as a final step.

        Returns:
            dict with keys:
            - 'sequence': List of lists [[step_0_nodes], [step_1_nodes], ...]
            - 'processed_nodes': Set of all nodes in the sequence
            - 'remaining_nodes': List of nodes not added to sequence
            - 'remaining_source_nodes': List of remaining nodes that are source nodes
            - 'remaining_non_source_nodes': List of remaining nodes that are not source nodes
            - 'complete': True if all nodes were sequenced, False otherwise
        """
        # Use graph attributes as defaults
        if starting_nodes is None:
            starting_nodes = getattr(self.graph, "starting_nodes", [])
        if stopping_nodes is None:
            stopping_nodes = getattr(self.graph, "stopping_nodes", [])

        # Convert to sets for O(1) lookups
        stopping_set = set(stopping_nodes)
        all_nodes = set(self.graph.nodes)

        if node_sort_key is None:
            node_sort_key = self._default_sequence_sort_key

        # Build successor map for efficient traversal
        successor_map = self.graph.BuildSuccessorMap()

        # Initialize tracking structures
        # - dependency_ready_set: nodes considered "ready" for dependency checks.
        #   Includes pre-marked nodes (e.g., sources/containers prepared for
        #   forward processing) so readiness checks can use existing values.
        # - processed_set: nodes that have been explicitly added to sequence steps.
        dependency_ready_set = set(self._processed_nodes)
        processed_set = set()
        sequence = []  # List of steps, each step is a list of nodes

        # Step 0: Starting nodes are the first step
        if starting_nodes:
            step_0 = list(starting_nodes)
            sequence.append(step_0)
            processed_set.update(step_0)
            dependency_ready_set.update(step_0)

        # Current nodes whose successors we'll examine
        current_nodes = list(starting_nodes)

        # Main loop: keep adding steps until no more nodes can be added
        while current_nodes:
            # Collect all successor candidates from current nodes
            # (excluding successors of stopping_nodes)
            candidates = set()
            for node in current_nodes:
                if node not in stopping_set:
                    for successor in successor_map.get(node, []):
                        if successor not in processed_set:
                            candidates.add(successor)

            # Filter candidates: only those with ALL predecessors in processed_set
            ready_nodes = []
            for candidate in candidates:
                all_preds_processed = all(
                    pred in dependency_ready_set for pred in candidate.predecessors
                )
                if all_preds_processed:
                    ready_nodes.append(candidate)

            # If we found ready nodes, add them as the next step
            if ready_nodes:
                ready_nodes.sort(key=node_sort_key)
                sequence.append(ready_nodes)
                processed_set.update(ready_nodes)
                dependency_ready_set.update(ready_nodes)
                current_nodes = ready_nodes
            else:
                # No ready nodes found, stop the loop
                current_nodes = []

        # Optionally append remaining source nodes as final step.
        if include_remaining_source_nodes:
            from zorvan.Nodes.ContainerNode import ContainerNode

            remaining_sources = [
                n
                for n in self.graph.nodes
                if n not in processed_set
                and len(n.predecessors) == 0
                and not isinstance(n, ContainerNode)
                and getattr(n, "name", "") != "LearningRate"
            ]
            if remaining_sources:
                remaining_sources.sort(key=node_sort_key)
                sequence.append(remaining_sources)
                processed_set.update(remaining_sources)
                dependency_ready_set.update(remaining_sources)

        # Analyze remaining nodes
        remaining_nodes = [n for n in all_nodes if n not in processed_set]
        remaining_source_nodes = [
            n for n in remaining_nodes if len(n.predecessors) == 0
        ]
        remaining_non_source_nodes = [
            n for n in remaining_nodes if len(n.predecessors) > 0
        ]

        return {
            "sequence": sequence,
            "processed_nodes": processed_set,
            "remaining_nodes": remaining_nodes,
            "remaining_source_nodes": remaining_source_nodes,
            "remaining_non_source_nodes": remaining_non_source_nodes,
            "complete": len(remaining_nodes) == 0,
        }

    def ForwardProcessing(
        self,
        iterations=1,
        starting_nodes=None,
        stopping_nodes=None,
        node_sort_key=None,
        include_remaining_source_nodes=False,
        exec_options: Optional[ExecutionOptions] = None,
        on_iteration_complete=None,
        on_step_complete=None,
        controller: Optional["GraphProcessor.ExecutionController"] = None,
    ):
        """
        Execute forward processing using the computed execution sequence.

        This method computes the execution sequence once, then iterates through
        the sequence for the specified number of iterations (epochs).

        Parameters:
        - iterations: Number of full passes through the sequence (epochs).
        - starting_nodes: Nodes to start execution from. Defaults to graph.starting_nodes.
        - stopping_nodes: Nodes that should not trigger successor activation.
        - node_sort_key: Optional callable for deterministic ordering of nodes
            within each sequence step.
        - include_remaining_source_nodes: If True, append remaining source nodes
            as a final step in the computed sequence.
        - exec_options: ExecutionOptions for pause/step control.
        - on_iteration_complete: Callback after each full pass (iteration/epoch).
        - on_step_complete: Callback after each step within a pass.
        - controller: Pre-existing ExecutionController.

        Returns:
            dict with execution statistics:
            - 'iterations_completed': Number of iterations actually completed
            - 'steps_per_iteration': Number of steps in the sequence
            - 'sequence_info': The result from find_execution_sequence()
        """
        # Compute execution sequence
        seq_result = self.find_execution_sequence(
            starting_nodes=starting_nodes,
            stopping_nodes=stopping_nodes,
            node_sort_key=node_sort_key,
            include_remaining_source_nodes=include_remaining_source_nodes,
        )
        sequence = seq_result["sequence"]

        if not sequence:
            return {
                "iterations_completed": 0,
                "steps_per_iteration": 0,
                "sequence_info": seq_result,
            }

        controller_obj = (
            controller
            if controller is not None
            else GraphProcessor.ExecutionController.from_options(exec_options)
        )

        iterations_completed = 0

        for iteration in range(iterations):
            # Clear processed nodes at the start of each iteration for fresh dimming cycle
            self._processed_nodes.clear()

            # Check stop signal
            if (
                getattr(controller_obj, "stop_event", None) is not None
                and controller_obj.stop_event.is_set()
            ):
                break

            # Process each step in the sequence
            for step_idx, step_nodes in enumerate(sequence):
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

                self.time += 1

                # Step completion callback
                if on_step_complete:
                    try:
                        on_step_complete(iteration + 1, step_idx + 1, step_nodes)
                    except Exception:
                        pass

                # Step interval for visualization
                interval = getattr(controller_obj, "step_interval_ms", None)
                if interval:
                    time.sleep(interval / 1000.0)

            iterations_completed += 1

            # Iteration completion callback
            if on_iteration_complete:
                try:
                    on_iteration_complete(iteration + 1)
                except Exception:
                    pass

        return {
            "iterations_completed": iterations_completed,
            "steps_per_iteration": len(sequence),
            "sequence_info": seq_result,
        }

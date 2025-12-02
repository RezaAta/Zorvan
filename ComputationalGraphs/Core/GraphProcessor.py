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

    def ForwardProcessing(
        self,
        iterations,
        starting_nodes=None,
        stopping_nodes=None,
        stop_on_nth_hit=1,
        reactivate_nodes=None,
        reactivate_interval=None,
        exec_options: Optional[ExecutionOptions] = None,
        controller=None,
    ):
        if not hasattr(self, "_successor_map"):
            self._successor_map = self.graph.BuildSuccessorMap()
        if not hasattr(self, "_predecessor_count"):
            self._predecessor_count = {
                node: len(node.predecessors) for node in self.graph.nodes
            }
        # _required_predecessor_count is the effective number of predecessors
        # a node must wait for before becoming active. It may be reduced
        # when we treat some predecessors (sources, container weights, etc.)
        # as pre-contributed during preparation.
        if not hasattr(self, "_required_predecessor_count"):
            # initialize as a copy of the original predecessor counts
            self._required_predecessor_count = dict(self._predecessor_count)
        if (
            not hasattr(self, "_forward_state_initialized")
            or not self._forward_state_initialized
        ):
            self._initialize_forward_state(starting_nodes)

        stopping_nodes_set = (
            set(stopping_nodes)
            if stopping_nodes is not None
            else set(getattr(self.graph, "stopping_nodes", []))
        )
        reactivate_nodes_set = set(reactivate_nodes) if reactivate_nodes else set()

        from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode

        # If no external controller provided, create one from options
        if controller is None:
            controller_obj = GraphProcessor.ExecutionController.from_options(
                exec_options
            )
        else:
            controller_obj = controller

        for _ in range(iterations):
            # Respect stop/pause if controller is available
            if (
                getattr(controller_obj, "stop_event", None) is not None
                and controller_obj.stop_event.is_set()
            ):
                break
            if getattr(controller_obj, "pause_event", None) is not None:
                while controller_obj.pause_event.is_set():
                    time.sleep(0.01)
            if (
                reactivate_interval
                and reactivate_nodes_set
                and getattr(self, "_iteration_counter", 0) > 0
            ):
                if self._iteration_counter % reactivate_interval == 0:
                    for node in reactivate_nodes_set:
                        if node in self.graph.nodes:
                            self._node_status[node] = "active"
                            if node not in self._active_nodes:
                                self._active_nodes.append(node)
                            self._processed_predecessor_count[node] = 0
                            if isinstance(node, DataStreamNode):
                                node.AdvanceStream()

            # Expose which nodes are currently being processed for UI highlighting
            try:
                self._currently_processing_nodes = list(self._active_nodes)
            except Exception:
                self._currently_processing_nodes = []

            if not self._active_nodes:
                # Clear currently processing nodes if nothing to do
                self._currently_processing_nodes = []
                break

            newly_processed = []
            for node in list(self._active_nodes):
                if not getattr(node, "midCalculation", False):
                    node.UpdateInputs()
                node.ProcessBatch()
                if not getattr(node, "midCalculation", False):
                    self._node_status[node] = "processed"
                    newly_processed.append(node)

            # Update currently processing nodes to the nodes that were just processed
            try:
                self._currently_processing_nodes = list(newly_processed)
            except Exception:
                self._currently_processing_nodes = []

            next_active = []
            for node in newly_processed:
                if node in stopping_nodes_set:
                    continue
                for successor in self._successor_map.get(node, []):
                    if self._node_status.get(successor) in ("active", "processed"):
                        continue
                    # increment the processed count for this successor and
                    # compare against the required-predecessor-count (which
                    # may have been reduced during preparation)
                    self._processed_predecessor_count[successor] += 1
                    required = self._required_predecessor_count.get(
                        successor, self._predecessor_count.get(successor, 0)
                    )
                    if self._processed_predecessor_count[successor] >= required:
                        next_active.append(successor)
                        self._node_status[successor] = "active"

            self._active_nodes = [
                n for n in self._active_nodes if getattr(n, "midCalculation", False)
            ] + next_active

            # If all nodes have become 'processed' (no 'unprocessed' remaining),
            # perform a cycle reset so the graph can run another pass.
            try:
                # Determine if every node has reached 'processed' state.
                all_processed = all(
                    status == "processed" for status in self._node_status.values()
                )
            except Exception:
                all_processed = False

            if all_processed:
                # Reset statuses and processed-predecessor counters
                for node in list(self._node_status.keys()):
                    self._node_status[node] = "unprocessed"
                    self._processed_predecessor_count[node] = 0

                # Clear any soft-processed tracking so helpers can reapply
                if hasattr(self, "_soft_processed_sources"):
                    del self._soft_processed_sources
                if hasattr(self, "_soft_processed_containers"):
                    del self._soft_processed_containers

                # Reapply container soft-preparations if helper exists (weights should be soft-contributors)
                if hasattr(self, "mark_container_nodes_as_processed"):
                    try:
                        self.mark_container_nodes_as_processed()
                    except Exception:
                        pass

                # Activate source nodes (no predecessors) so they are processed
                # first in the next pass (this ensures DataStreamNodes advance).
                source_nodes = [
                    node for node in self.graph.nodes if len(node.predecessors) == 0
                ]
                self._active_nodes = []
                for node in source_nodes:
                    # Reset processed counter for the node
                    self._processed_predecessor_count[node] = 0
                    # Set node to active so it will be processed in the next iteration
                    self._node_status[node] = "active"
                    if node not in self._active_nodes:
                        self._active_nodes.append(node)
                    # If this is a DataStreamNode, advance its stream to the next sample
                    try:
                        if isinstance(node, DataStreamNode):
                            node.AdvanceStream()
                    except Exception:
                        pass

                # Note: starting nodes will become active naturally after source nodes
                # are processed and increment their successors' processed counts.

            self._iteration_counter = getattr(self, "_iteration_counter", 0) + 1
            self.time += 1

        return len(self._active_nodes)

    def ManualProcessing(
        self,
        iterations,
        computation_sequence=None,
        wrap_sequence=True,
        exec_options: Optional[ExecutionOptions] = None,
        controller=None,
        on_iteration_complete=None,
    ):
        """
        Manual processing mode: the user provides a sequence of node groups (list of iterables),
        each group is processed in one iteration (in the order provided). This method does no
        graph initialization or dependency resolution — it simply calls UpdateInputs() and
        ProcessBatch() for each node in the sequence for each iteration. If no sequence is
        provided, falls back to forward processing.
        """
        # Prefer local controller if provided, otherwise create one from exec_options
        controller_obj = (
            controller
            if controller is not None
            else GraphProcessor.ExecutionController.from_options(exec_options)
        )

        # If a computation_sequence was provided, validate and set it on the graph
        if computation_sequence is not None:
            # Use graph helper to validate/resolve sequence; this also sets it on the graph
            try:
                self.graph.set_manual_processing_sequence(
                    computation_sequence, strict=True
                )
            except Exception:
                # If strict resolution fails, fallback to forward processing
                return self.ForwardProcessing(
                    iterations,
                    exec_options=exec_options,
                    controller=controller,
                    starting_nodes=None,
                )

        sequence = getattr(self.graph, "manual_processing_sequence", None)
        if not sequence:
            # No sequence configured; fallback to forward processing
            # Note: ForwardProcessing handles graph initialization itself.
            return self.ForwardProcessing(
                iterations,
                exec_options=exec_options,
                controller=controller,
                starting_nodes=None,
            )

        seq_len = len(sequence)
        # initialize stored manual sequence and index if not present
        if not hasattr(self, "_manual_sequence") or self._manual_sequence != sequence:
            self._manual_sequence = sequence
            self._manual_sequence_index = 0
        if not hasattr(self, "_manual_sequence_index"):
            self._manual_sequence_index = 0

        for t in range(iterations):
            # Respect controller stop/pause if requested
            if (
                getattr(controller_obj, "stop_event", None) is not None
                and controller_obj.stop_event.is_set()
            ):
                break
            if (
                getattr(controller_obj, "pause_event", None) is not None
                and controller_obj.pause_event.is_set()
            ):
                while controller_obj.pause_event.is_set():
                    time.sleep(0.01)

            # Get the current set of nodes to process this iteration
            active_set = sequence[self._manual_sequence_index]

            # Expose for UI (empty if not used)
            try:
                self._currently_processing_nodes = list(active_set)
            except Exception:
                self._currently_processing_nodes = []

            # Process each node in the set in order provided
            for node in active_set:
                # Minimal processing: update inputs if not midCalculation, then process
                try:
                    if not getattr(node, "midCalculation", False):
                        node.UpdateInputs()
                    node.ProcessBatch()
                except Exception:
                    # Node processing errors do not stop manual processing; continue to others
                    continue

            # Advance sequence index
            self._manual_sequence_index += 1
            if self._manual_sequence_index >= seq_len:
                if wrap_sequence:
                    self._manual_sequence_index = 0
                else:
                    # If no wrap and we exhausted sequence, stop processing
                    break

            self.time += 1
            if on_iteration_complete:
                try:
                    on_iteration_complete(t + 1)
                except Exception:
                    pass

        return

    def reset_manual_state(self):
        """Reset the manual processing internal state for sequence position and cached sequence."""
        if hasattr(self, "_manual_sequence_index"):
            del self._manual_sequence_index
        if hasattr(self, "_manual_sequence"):
            del self._manual_sequence

        return

    def _initialize_forward_state(self, starting_nodes=None):
        self._forward_state_initialized = True
        self._node_status = {node: "unprocessed" for node in self.graph.nodes}
        self._processed_predecessor_count = {node: 0 for node in self.graph.nodes}
        # Initialize required predecessor counts (may be reduced by
        # preparations such as marking sources/containers as pre-contributed)
        if not hasattr(self, "_predecessor_count"):
            self._predecessor_count = {
                node: len(node.predecessors) for node in self.graph.nodes
            }
        self._required_predecessor_count = dict(self._predecessor_count)
        if starting_nodes is not None:
            self._active_nodes = list(starting_nodes)
        elif hasattr(self.graph, "starting_nodes") and self.graph.starting_nodes:
            self._active_nodes = list(self.graph.starting_nodes)
        else:
            self._active_nodes = [
                node for node in self.graph.nodes if len(node.predecessors) == 0
            ]
        self._starting_nodes_cache = list(self._active_nodes)
        for node in self._active_nodes:
            self._node_status[node] = "active"

    def reset_forward_state(self):
        self._forward_state_initialized = False
        self._iteration_counter = 0
        # Clear any preparation markers so subsequent Prepare/initialization
        # can recompute required counts and reapply soft contributions.
        if hasattr(self, "_soft_processed_containers"):
            del self._soft_processed_containers
        if hasattr(self, "_soft_processed_sources"):
            del self._soft_processed_sources
        if hasattr(self, "_required_predecessor_count"):
            del self._required_predecessor_count

    def mark_source_nodes_as_processed(self):
        """Mark all source nodes (no predecessors) as 'processed' for forward processing.

        This also updates the processor's internal processed-predecessor counters and
        activates any successors that become ready as a result.
        Returns the number of source nodes marked.
        """
        if not hasattr(self, "_successor_map"):
            self._successor_map = self.graph.BuildSuccessorMap()
        if not hasattr(self, "_predecessor_count"):
            self._predecessor_count = {
                node: len(node.predecessors) for node in self.graph.nodes
            }
        if (
            not hasattr(self, "_forward_state_initialized")
            or not self._forward_state_initialized
        ):
            self._initialize_forward_state()

        # Consider source nodes as nodes with no predecessors, but exclude
        # ContainerNode instances (weights) which we handle separately.
        # Consider source nodes as nodes with no predecessors. ContainerNode
        # instances are intentionally NOT excluded here so that special-case
        # sources (e.g., LearningRate implemented as a DisplayNode) or
        # container-like sources can be prepared via this helper.
        source_nodes = [n for n in self.graph.nodes if len(n.predecessors) == 0]
        count = 0
        for src in source_nodes:
            if self._node_status.get(src) != "processed":
                self._node_status[src] = "processed"
                count += 1
                # Increment processed predecessor count for successors to
                # indicate that this source predecessor is available.
                # Track applied sources to avoid double-applying.
                if not hasattr(self, "_soft_processed_sources"):
                    self._soft_processed_sources = set()
                if src not in self._soft_processed_sources:
                    self._soft_processed_sources.add(src)
                    for succ in self._successor_map.get(src, []):
                        self._processed_predecessor_count[succ] = (
                            self._processed_predecessor_count.get(succ, 0) + 1
                        )
                        # Activate successor if it now meets the required count
                        req = self._required_predecessor_count.get(
                            succ, self._predecessor_count.get(succ, 0)
                        )
                        if self._processed_predecessor_count[succ] >= req:
                            if self._node_status.get(succ) not in (
                                "active",
                                "processed",
                            ):
                                self._node_status[succ] = "active"
                                if succ not in self._active_nodes:
                                    self._active_nodes.append(succ)

        return count

    def mark_container_nodes_as_processed(self):
        """Mark ContainerNode instances as 'processed'.

        Useful for marking weight ContainerNodes as processed before the first forward pass.
        Returns the number of container nodes marked.
        """
        try:
            from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
        except Exception:
            # If import fails, no container nodes to mark
            return 0

        # Do NOT mark container nodes as fully 'processed' here. Marking them
        # as processed prevents them from later being processed when gradient
        # updates (dW) arrive. Instead, treat container nodes as "soft-contributors"
        # to successor readiness: reduce the required-predecessor-count for
        # successors so those nodes become ready, but keep the container
        # node itself unprocessed so it can be updated later.
        if not hasattr(self, "_successor_map"):
            self._successor_map = self.graph.BuildSuccessorMap()
        if not hasattr(self, "_predecessor_count"):
            self._predecessor_count = {
                node: len(node.predecessors) for node in self.graph.nodes
            }
        if (
            not hasattr(self, "_forward_state_initialized")
            or not self._forward_state_initialized
        ):
            self._initialize_forward_state()

        # Keep a set of soft-processed container nodes for debugging/inspection
        if not hasattr(self, "_soft_processed_containers"):
            self._soft_processed_containers = set()

        count = 0
        for node in self.graph.nodes:
            if isinstance(node, ContainerNode):
                if node not in self._soft_processed_containers:
                    self._soft_processed_containers.add(node)
                    count += 1
                    # Increment successors' processed counts to represent
                    # that the weight predecessor is available for them.
                    # The container node itself is NOT marked processed so it
                    # can still be updated later by gradient predecessors.
                    for succ in self._successor_map.get(node, []):
                        self._processed_predecessor_count[succ] = (
                            self._processed_predecessor_count.get(succ, 0) + 1
                        )
                        req = self._required_predecessor_count.get(
                            succ, self._predecessor_count.get(succ, 0)
                        )
                        if self._processed_predecessor_count[succ] >= req:
                            if self._node_status.get(succ) not in (
                                "active",
                                "processed",
                            ):
                                self._node_status[succ] = "active"
                                if succ not in self._active_nodes:
                                    self._active_nodes.append(succ)

        return count

    def __repr__(self):
        return f"GraphProcessor with {len(self.graph.nodes)} nodes at time={self.time}."

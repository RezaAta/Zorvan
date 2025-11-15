from concurrent.futures import ThreadPoolExecutor
import math
import os

class GraphProcessor:
    def __init__(self, graph, max_workers=None, verbose=True, visual = False, auto_threading=True, chunk_size=None):
        self.graph = graph
        self.time = 0  # Initialize time for tracking iterations
        self.verbose = verbose  # Enable or disable printing
        self.visual = visual
        self.auto_threading = auto_threading  # Automatically choose threading mode
        
        # Auto-detect optimal number of workers
        num_nodes = len(graph.nodes)
        if max_workers is None:
            self.max_workers = self._calculate_optimal_workers(num_nodes)
            self._auto_workers = True  # Track that we auto-selected
        else:
            self.max_workers = max_workers
            self._auto_workers = False
        
        # Improved heuristic: Use single-thread for small/medium graphs
        # Based on empirical results, Python threading overhead (GIL + task management)
        # dominates until graphs are very large (500+ nodes)
        nodes_per_worker = num_nodes / self.max_workers if self.max_workers > 0 else num_nodes
        
        if auto_threading:
            # Very conservative threshold based on empirical data:
            # Single-thread wins until graphs are massive (1000+ nodes)
            # AND well-distributed across workers (100+ nodes per worker)
            self.use_single_thread_mode = (num_nodes < 1000) or (nodes_per_worker < 100)
        else:
            self.use_single_thread_mode = False
        
        # Chunking: Process multiple nodes per task to reduce overhead
        # Goal: Create chunks that balance parallelism vs overhead
        if chunk_size is None:
            # Adaptive chunking: larger chunks for smaller graphs
            if num_nodes < 100:
                # Small graphs: 1-2 tasks per worker to minimize overhead
                self.chunk_size = max(10, num_nodes // (self.max_workers * 2))
            else:
                # Large graphs: 3-4 tasks per worker for better load balancing
                self.chunk_size = max(5, num_nodes // (self.max_workers * 4))
        else:
            self.chunk_size = chunk_size
    
    def _calculate_optimal_workers(self, num_nodes):
        """
        Calculate optimal number of worker threads based on:
        1. CPU core count
        2. Graph size
        3. Expected overhead vs parallelism benefit
        
        Note: For typical computational graph operations (small per-node work),
        single-threading often wins due to Python GIL and threading overhead.
        Multi-threading mainly helps with very large graphs (1000+ nodes) or
        when nodes do CPU-intensive work that releases the GIL (NumPy, etc.)
        """
        # Get CPU count (fallback to 4 if unavailable)
        try:
            cpu_count = os.cpu_count() or 4
        except Exception:
            cpu_count = 4
        
        # Very conservative rules based on empirical results:
        # For typical computational graphs with Python operations,
        # GIL + threading overhead dominates until graphs are HUGE
        if num_nodes < 1000:
            # Small/medium/large graphs: Single thread is faster
            # (GIL prevents true parallelism, overhead dominates)
            return 1
        elif num_nodes < 2000:
            # Very large graphs: Try minimal parallelism
            return min(2, cpu_count // 4)
        else:
            # Massive graphs: Use modest parallelism
            # (Still limited by GIL for pure Python operations)
            return min(4, cpu_count // 2)
    
    def _chunk_nodes(self, nodes):
        """Split nodes into chunks for batch processing."""
        for i in range(0, len(nodes), self.chunk_size):
            yield nodes[i:i + self.chunk_size]
    
    def _process_node_chunk(self, nodes, method_name):
        """Process a chunk of nodes by calling the specified method on each."""
        for node in nodes:
            getattr(node, method_name)()

    def ComputeGraph(self, iterations=1):
        """
        Perform synchronous parallel computation for the graph over a number of iterations.
        Each node first updates its inputs, then performs operations in two separate parallel loops.
        Automatically uses single-threaded mode for small graphs to avoid threading overhead.
        """
        # Auto-select single-threaded mode for small graphs
        if self.use_single_thread_mode:
            if self.verbose:
                worker_info = f" (auto-selected {self.max_workers} workers)" if self._auto_workers else ""
                print(f"Auto-selected single-threaded mode ({len(self.graph.nodes)} nodes{worker_info})")
            return self.ComputeGraphSingleThread(iterations)
        
        if self.verbose:
            worker_info = f" with {self.max_workers} workers"
            if self._auto_workers:
                worker_info += " (auto-selected)"
            print(f"Starting graph computation for {iterations} iterations{worker_info}...")

        if self.verbose:
            print("\n--- Time Step 0 ---")
            for node in self.graph.nodes:
                print(f"Node {node.name} has new value: {node.value}")

        # Create thread pool once and reuse across all iterations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for t in range(iterations):
                if self.verbose:
                    print(f"\n--- Time Step {t+1} ---")
            
                # 1. First loop: Update the inputs for all nodes in parallel (chunked)
                nodes_to_update = [node for node in self.graph.nodes if not node.midCalculation]
                
                # Split nodes into chunks and process each chunk in parallel
                chunks = list(self._chunk_nodes(nodes_to_update))
                list(executor.map(lambda chunk: self._process_node_chunk(chunk, 'UpdateInputs'), chunks))

                # 2. Second loop: Process the batch for each node in parallel (chunked)
                chunks = list(self._chunk_nodes(self.graph.nodes))
                list(executor.map(lambda chunk: self._process_node_chunk(chunk, 'ProcessBatch'), chunks))

                # Print node values after processing
                if self.verbose:
                    for node in self.graph.nodes:
                        print(f"Node {node.name} has new value: {node.value}")

                # Increment time after completing the time step
                self.time += 1
                if self.verbose:
                    print(f"End of time step {t+1}. Time is now {self.time}.")

                if self.visual:
                    self.graph.DisplayGraph(fileName = f"iteratin{t}")
                
    def ComputeGraphSingleThread(self, iterations=1):

        if self.verbose:
            print(f"Starting graph computation for {iterations} iterations...")

            print("\n--- Time Step 0 ---")
            for node in self.graph.nodes:
                print(f"Node {node.name} has new value: {node.value}")

        for t in range(iterations):
            if self.verbose:
                print(f"\n--- Time Step {t+1} ---")
            for node in self.graph.nodes: 
                if not node.midCalculation:
                    node.UpdateInputs() 
            for node in self.graph.nodes:
                node.ProcessBatch() 

            # Print node values after processing
            if self.verbose:
                for node in self.graph.nodes:
                    print(f"Node {node.name} has new value: {node.value}")

            # Increment time after completing the time step
            self.time += 1
            if self.verbose:
                print(f"End of time step {t+1}. Time is now {self.time}.")

            if self.visual:
                self.graph.DisplayGraph(fileName = f"iteratin{t}")

    def ForwardProcessing(self, iterations=1, starting_nodes=None, stopping_nodes=None, stop_on_nth_hit=1,
                         reactivate_nodes=None, reactivate_interval=None):
        """
        Execute graph using forward processing - process active nodes only.
        
        Single-batch semantics: Each iteration processes ONE batch of currently active nodes.
        This provides fine-grained control and observability for step-by-step execution.
        
        Active nodes are determined by:
        1. Nodes with all predecessors processed
        2. Nodes in midCalculation state (multi-batch processing)
        
        Stopping nodes (automata-style termination):
        - When a stopping node is processed for the nth time, execution halts
        - Useful for graphs with cycles or when you want explicit termination control
        
        Node reactivation (for cyclic training):
        - Specified nodes can be reactivated every N iterations
        - Useful for input/label nodes that need to restart after each training pass
        - Reactivation happens BEFORE processing the reactivation iteration
        
        Starting nodes priority (cascading):
        1. Use starting_nodes parameter if provided (highest priority)
        2. Use graph.starting_nodes if set
        3. Auto-detect: nodes with no predecessors (fallback)
        
        Args:
            iterations: Number of timesteps to process. Default=1
            starting_nodes: List of nodes to start with (overrides graph.starting_nodes)
            stopping_nodes: List of nodes that trigger termination when reached (None = no stopping nodes)
            stop_on_nth_hit: Stop when any stopping node is processed this many times. Default=1
            reactivate_nodes: List of nodes to reactivate periodically (e.g., input nodes)
            reactivate_interval: Reactivate nodes every N iterations (None = no reactivation)
        
        Returns:
            int: Number of active nodes remaining after execution
        """
        # Initialize persistent state on first call
        if not hasattr(self, '_forward_state_initialized') or not self._forward_state_initialized:
            self._initialize_forward_state(starting_nodes)
        
        # Initialize iteration counter if not exists
        if not hasattr(self, '_iteration_counter'):
            self._iteration_counter = 0
        
        # Build maps once for efficiency
        if not hasattr(self, '_successor_map'):
            self._successor_map = self.graph.BuildSuccessorMap()
            self._predecessor_count = {node: len(node.predecessors) for node in self.graph.nodes}
        
        # Convert stopping_nodes to set for efficient lookup. If not provided,
        # fall back to `graph.stopping_nodes` (new repurposed mechanic).
        if stopping_nodes is not None:
            stopping_nodes_set = set(stopping_nodes)
        else:
            stopping_nodes_set = set(getattr(self.graph, 'stopping_nodes', []))
        
        # Convert reactivate_nodes to set for efficient lookup
        reactivate_nodes_set = set(reactivate_nodes) if reactivate_nodes else set()
        # Use explicit DataStreamNode type checks instead of duck-typing
        from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
        
        # Process for requested number of iterations
        for iteration in range(iterations):
            # Check if we need to reactivate nodes BEFORE processing this iteration
            if reactivate_interval and reactivate_nodes_set and self._iteration_counter > 0:
                if self._iteration_counter % reactivate_interval == 0:
                    if self.verbose:
                        print(f"\n{'='*60}")
                        print(f"Reactivating {len(reactivate_nodes_set)} nodes at iteration {self._iteration_counter}")
                        print(f"{'='*60}")
                    
                    # Reactivate specified nodes
                    for node in reactivate_nodes_set:
                        if node in self.graph.nodes:
                            # Reset node's processed status to active
                            self._node_status[node] = 'active'
                            # Add to active nodes if not already there
                            if node not in self._active_nodes:
                                self._active_nodes.append(node)
                            # Reset predecessor count for this node (it's starting fresh)
                            self._processed_predecessor_count[node] = 0
                            
                            # If this is a DataStreamNode, advance its stream to next sample
                            if isinstance(node, DataStreamNode):
                                node.AdvanceStream()
                            
                            if self.verbose:
                                print(f"  Reactivated: {node.name}")
            
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Forward Processing - Iteration {iteration + 1}/{iterations} (Global iteration: {self._iteration_counter + 1})")
                print(f"{'='*60}")
            
            if not self._active_nodes:
                if self.verbose:
                    # Diagnostic: why did we stop?
                    unprocessed = [n.name for n, s in self._node_status.items() if s == 'unprocessed']
                    processed = [n.name for n, s in self._node_status.items() if s == 'processed']
                    print(f"\n*** No active nodes - execution stopping ***")
                    print(f"*** Unprocessed: {len(unprocessed)} nodes: {unprocessed[:10]}...")
                    print(f"*** Processed: {len(processed)} nodes")
                break
            
            if self.verbose:
                print(f"Active nodes: {len(self._active_nodes)}")
            
            # Store currently processing nodes for GUI highlighting
            self._currently_processing_nodes = list(self._active_nodes)
            
            # Process all currently active nodes
            newly_processed = []
            for node in self._active_nodes:
                # Skip UpdateInputs if node is midCalculation (continuing multi-batch)
                if not node.midCalculation:
                    node.UpdateInputs()
                    if self.verbose:
                        print(f"  {node.name}: inputs={node.inputs}")
                
                # Always call ProcessBatch (handles midCalculation internally)
                node.ProcessBatch()
                
                if self.verbose:
                    print(f"  {node.name}: value={node.value}, midCalc={node.midCalculation}")
                
                # NOTE: `stopping_nodes` have been repurposed: they now suppress
                # successor candidation when processed (they do NOT terminate
                # the entire ForwardProcessing run). The old termination logic
                # has been removed in favor of this behavior.
                
                # Only mark as processed if NOT in midCalculation
                # (midCalculation nodes need to be processed again next iteration)
                if not node.midCalculation:
                    self._node_status[node] = 'processed'
                    newly_processed.append(node)
                    if self.verbose:
                        print(f"  [DBG] Marked processed: {node.name}")
                else:
                    # Stay active for next iteration
                    if self.verbose:
                        print(f"  {node.name}: still midCalculation, will process again")
            
            # Find newly ready successors from processed nodes
            next_active = []
            for node in newly_processed:
                # If this node is a configured stopping node, skip successor candidation.
                # Stopping nodes now mean: "do not candidate successors when I am processed".
                if node in stopping_nodes_set:
                    if self.verbose:
                        print(f"  {node.name}: stopping node processed — suppressing successor candidation")
                    continue

                # Check successors of this newly processed node
                for successor in self._successor_map.get(node, []):
                    # Skip successors that are already active
                    if self._node_status.get(successor) == 'active':
                        continue

                    # If successor is already marked 'processed', skip it.
                    # Reactivation of processed successors is disabled here; the
                    # `stopping_nodes` mechanism controls which nodes suppress
                    # successor candidation (e.g., weight ContainerNodes).
                    if self._node_status.get(successor) == 'processed':
                        continue

                    # Increment processed predecessor count for this successor
                    self._processed_predecessor_count[successor] += 1

                    # TEMP DEBUG: print predecessor statuses and counts
                    if self.verbose:
                        pred_statuses = [(p.name, self._node_status.get(p), len(p.predecessors)) for p in successor.predecessors]
                        print(f"    [DBG] Successor={successor.name}: preds={pred_statuses}")
                        print(f"    [DBG]    -> prior_count={self._processed_predecessor_count[successor]-1}/{self._predecessor_count[successor]} -> new_count={self._processed_predecessor_count[successor]}/{self._predecessor_count[successor]}")

                    # Compute effective processed count by adding any predecessor
                    # nodes that are in the stopping-nodes set (these are treated
                    # as not blocking activation even if unprocessed).
                    stopping_extra = 0
                    try:
                        stopping_set = stopping_nodes_set
                    except NameError:
                        stopping_set = set()

                    for pred in successor.predecessors:
                        if pred in stopping_set and self._node_status.get(pred) != 'processed':
                            stopping_extra += 1

                    effective_processed = self._processed_predecessor_count[successor] + stopping_extra

                    # If effective processed count equals the total predecessor count,
                    # this successor is ready to be activated.
                    if effective_processed == self._predecessor_count[successor]:
                        next_active.append(successor)
                        self._node_status[successor] = 'active'
                        if self.verbose:
                            print(f"  -> {successor.name} now ready (all predecessors processed or stopping-nodes treated as ready) - activated by {node.name}")
                    else:
                        # If this successor is blocked only by source predecessors, reactivate those sources
                        unprocessed_source_preds = [
                            pred for pred in successor.predecessors
                            if self._node_status.get(pred) != 'processed'
                            and len(pred.predecessors) == 0  # Source node: no predecessors
                        ]

                        if unprocessed_source_preds:
                            # Reactivate all source predecessors immediately
                            for source_pred in unprocessed_source_preds:
                                # Avoid adding duplicates to next_active
                                if source_pred not in next_active and source_pred not in self._active_nodes:
                                    next_active.append(source_pred)
                                    self._node_status[source_pred] = 'active'
                                    # Reset processed count so it will be recounted
                                    self._processed_predecessor_count[source_pred] = 0
                                    if self.verbose:
                                        print(f"  -> Reactivating source node {source_pred.name} (needed by {successor.name})")
            
            # Update active nodes: Keep midCalculation nodes + add newly ready nodes
            self._active_nodes = [n for n in self._active_nodes if n.midCalculation] + next_active
            
            # Check if we just finished processing source nodes and need to activate starting nodes
            if not self._active_nodes and hasattr(self, '_awaiting_starting_nodes') and self._awaiting_starting_nodes:
                # Source nodes have already been processed in the normal loop above
                # (they were marked 'processed' at line ~314 and successor counts incremented at line ~369)
                # Now we just need to activate starting nodes for the actual computation cycle
                
                if self.verbose:
                    print(f"\nSource nodes have been processed. Now activating starting nodes for computation")
                
                # Activate starting nodes for the actual computation cycle
                if hasattr(self, '_starting_nodes_cache'):
                    self._active_nodes = list(self._starting_nodes_cache)
                    for node in self._active_nodes:
                        self._node_status[node] = 'active'
                    
                    if self.verbose:
                        print(f"Activating {len(self._active_nodes)} starting nodes")
                
                # Clear the flag
                self._awaiting_starting_nodes = False
                
                # Continue to next iteration
                return len(self._active_nodes)
            
            # CRITICAL: Check for cycle completion BEFORE checking if active_nodes is empty
            # This allows cycle reset even when cyclic reactivation has created active nodes
            unprocessed_count = sum(1 for status in self._node_status.values() if status == 'unprocessed')
            active_count = sum(1 for status in self._node_status.values() if status == 'active')

            # Only consider cycle complete when there are no unprocessed nodes
            # AND there are no currently active nodes. Previously the reset
            # triggered when every node was either 'processed' or 'active',
            # which caused an immediate reset while some nodes had just been
            # activated for the next pass (e.g. W_x* weight nodes). That
            # cleared their 'active' state and prevented them from running.
            if unprocessed_count == 0 and active_count == 0:
                # All nodes are processed (active nodes may exist due to cyclic reactivation) - cycle complete!
                if self.verbose:
                    print(f"\n{'='*60}")
                    print("Cycle complete - preparing for next cycle")
                    print(f"{'='*60}")
                    # Debug: list node statuses prior to reset
                    processed_nodes = [n.name for n, s in self._node_status.items() if s == 'processed']
                    active_nodes = [n.name for n, s in self._node_status.items() if s == 'active']
                    unprocessed_nodes = [n.name for n, s in self._node_status.items() if s == 'unprocessed']
                    print(f"  [DBG] Before reset -> processed({len(processed_nodes)}): {processed_nodes[:10]}...")
                    print(f"  [DBG] Before reset -> active({len(active_nodes)}): {active_nodes[:10]}...")
                    print(f"  [DBG] Before reset -> unprocessed({len(unprocessed_nodes)}): {unprocessed_nodes[:10]}...")
                
                # Set the flag for testing
                self._cycle_reset_occurred = True
                
                # Reset all nodes to unprocessed for the next cycle
                reset_list = []
                for node in self.graph.nodes:
                    # Record for debug then reset
                    reset_list.append(node.name)
                    self._node_status[node] = 'unprocessed'
                    self._processed_predecessor_count[node] = 0

                if self.verbose:
                    print(f"  [DBG] Reset nodes -> cleared {len(reset_list)} nodes: {reset_list[:10]}...")
                
                # CRITICAL: First, activate source nodes (no predecessors) to update their data
                # This includes DataStreamNodes which need to advance to the next sample
                source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
                
                # NOTE: Do NOT mark ContainerNodes as processed here. Instead, we
                # will treat stopping-nodes (weights) as "not required to be
                # processed" for predecessor checks when deciding activation of
                # successors. This avoids prematurely marking weights processed
                # while allowing multiplication nodes to activate.

                # Filter source nodes: only activate sources that are DataStreamNodes
                # (can advance their own stream) OR nodes explicitly in the starting nodes cache.
                starting_cache = getattr(self, '_starting_nodes_cache', [])
                activatable_sources = [
                    n for n in source_nodes
                    if isinstance(n, DataStreamNode) or n in starting_cache
                ]

                if activatable_sources:
                    # Activate only the filtered source nodes to process first
                    self._active_nodes = list(activatable_sources)
                    for node in self._active_nodes:
                        self._node_status[node] = 'active'
                    
                    if self.verbose:
                        print(f"Activating {len(self._active_nodes)} source nodes to update data")
                        print(f"  Source nodes: {[n.name for n in self._active_nodes[:5]]}...")
                        print(f"  Active nodes list length: {len(self._active_nodes)}")
                    
                    # After source nodes process, starting nodes will be activated in the next iteration
                    # Set a flag to indicate we need to activate starting nodes after sources finish
                    self._awaiting_starting_nodes = True
                else:
                    # No activatable source nodes; reactivate starting nodes directly if available
                    if hasattr(self, '_starting_nodes_cache') and self._starting_nodes_cache:
                        self._active_nodes = list(self._starting_nodes_cache)
                        for node in self._active_nodes:
                            self._node_status[node] = 'active'
                        
                        if self.verbose:
                            print(f"Reactivated {len(self._active_nodes)} starting nodes for next cycle")
                
                # Continue to next iteration (don't return, let the loop continue)
            
            # If no active nodes but there are unprocessed nodes, check if source reactivation can help
            if not self._active_nodes:
                unprocessed_count = sum(1 for status in self._node_status.values() if status == 'unprocessed')
                
                # If we have unprocessed nodes but no active nodes, check if source reactivation can help
                if unprocessed_count > 0:
                    if self.verbose:
                        print(f"\n  No active nodes, but {unprocessed_count} unprocessed nodes remain")
                        print("  Checking if source nodes need reactivation...")
                    
                    # Check all unprocessed nodes to see if they're blocked only by source predecessors
                    reactivated_sources = []
                    for node in self.graph.nodes:
                        if self._node_status.get(node, 'unprocessed') == 'unprocessed':
                            # Check what's blocking this node
                            unprocessed_preds = [
                                pred for pred in node.predecessors
                                if self._node_status.get(pred, 'unprocessed') != 'processed'
                            ]
                            
                            # If only source nodes are blocking, reactivate them
                            source_preds = [
                                pred for pred in unprocessed_preds
                                if len(pred.predecessors) == 0  # Source node
                            ]
                            
                            if source_preds and len(source_preds) == len(unprocessed_preds):
                                # All unprocessed predecessors are sources - reactivate them!
                                for source_pred in source_preds:
                                    if source_pred not in reactivated_sources:
                                        reactivated_sources.append(source_pred)
                                        self._node_status[source_pred] = 'active'
                                        self._processed_predecessor_count[source_pred] = 0
                                        if self.verbose:
                                            print(f"    Reactivating source {source_pred.name} (blocks {node.name})")
                    
                    # Add reactivated sources to active list
                    if reactivated_sources:
                        self._active_nodes = reactivated_sources
                        if self.verbose:
                            print(f"  Reactivated {len(reactivated_sources)} source nodes")
            
            # Increment iteration counter (for reactivation tracking)
            self._iteration_counter += 1
            
            # Increment time counter
            self.time += 1
            
            # Optional visualization
            if self.visual:
                self.graph.DisplayGraph(fileName=f"forward_iter_{iteration}")
        
        return len(self._active_nodes)
    
    def _initialize_forward_state(self, starting_nodes=None):
        """
        Initialize persistent state for forward processing.
        Called automatically on first ForwardProcessing() call.
        
        Starting nodes priority (cascading):
        1. Use starting_nodes parameter if provided
        2. Use graph.starting_nodes if set
        3. Auto-detect: nodes with no predecessors
        
        Args:
            starting_nodes: Optional list of nodes to start execution from
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"INITIALIZING FORWARD STATE")
            print(f"{'='*60}")
            print(f"Param starting_nodes: {starting_nodes}")
            print(f"Graph has 'starting_nodes': {hasattr(self.graph, 'starting_nodes')}")
            if hasattr(self.graph, 'starting_nodes'):
                print(f"Graph.starting_nodes: {self.graph.starting_nodes}")
                if self.graph.starting_nodes:
                    print(f"Names: {[n.name for n in self.graph.starting_nodes]}")
            print(f"{'='*60}\n")
        
        self._forward_state_initialized = True
        self._node_status = {node: 'unprocessed' for node in self.graph.nodes}
        self._processed_predecessor_count = {node: 0 for node in self.graph.nodes}
        # Stopping-nodes hit counter removed. Stopping nodes are repurposed
        # to suppress successor candidation; no hit-count termination behavior.
        
        # Determine starting nodes using cascading priority
        if starting_nodes is not None:
            # Priority 1: Use parameter if provided
            self._active_nodes = list(starting_nodes)
            if self.verbose:
                print(f"Starting nodes: Using parameter ({len(self._active_nodes)} nodes)")
        elif hasattr(self.graph, 'starting_nodes') and self.graph.starting_nodes:
            # Priority 2: Use graph's starting_nodes property
            self._active_nodes = list(self.graph.starting_nodes)
            if self.verbose:
                print(f"Starting nodes: Using graph.starting_nodes ({len(self._active_nodes)} nodes)")
        else:
            # Priority 3: Auto-detect nodes with no predecessors
            self._active_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
            if self.verbose:
                print(f"Starting nodes: Auto-detected sources ({len(self._active_nodes)} nodes)")
        
        # Cache starting nodes for cycle resets
        self._starting_nodes_cache = list(self._active_nodes)
        
        # Mark starting nodes as active
        for node in self._active_nodes:
            self._node_status[node] = 'active'
    
    def reset_forward_state(self):
        """
        Reset forward processing state to restart execution from the beginning.
        Call this when you want to start a new execution cycle.
        """
        self._forward_state_initialized = False
        self._iteration_counter = 0  # Reset iteration counter
        if hasattr(self, '_active_nodes'):
            del self._active_nodes
        if hasattr(self, '_node_status'):
            del self._node_status
        if hasattr(self, '_processed_predecessor_count'):
            del self._processed_predecessor_count
    
    def mark_source_nodes_as_processed(self):
        """
        Mark all source nodes (nodes with no predecessors) as 'processed'.
        
        This is useful for MLP/neural network graphs where:
        - Input nodes (DataStreamNode) have values loaded
        - Weight nodes (ContainerNode) have initial values
        - These nodes don't need to "process" - their values are already available
        
        Call this AFTER initializing forward state but BEFORE starting processing.
        Typically used for MLPGraphForwardProcessing before training.
        
        Example usage:
            processor = GraphProcessor(mlp_graph)
            processor.ForwardProcessing(iterations=1)  # Initialize state
            processor.mark_source_nodes_as_processed()
            processor.ForwardProcessing(iterations=remaining_iterations)
        
        Returns:
            int: Number of source nodes marked as processed
        """
        if not hasattr(self, '_forward_state_initialized') or not self._forward_state_initialized:
            # Initialize state first
            self._initialize_forward_state()
        
        # Initialize any nodes that were added after state initialization
        for node in self.graph.nodes:
            if node not in self._node_status:
                self._node_status[node] = 'unprocessed'
                self._processed_predecessor_count[node] = 0
        
        # Rebuild maps if needed (graph may have changed)
        self._successor_map = self.graph.BuildSuccessorMap()
        self._predecessor_count = {node: len(node.predecessors) for node in self.graph.nodes}
        
        # Find all source nodes (no predecessors)
        source_nodes = [node for node in self.graph.nodes if len(node.predecessors) == 0]
        
        marked_count = 0
        for node in source_nodes:
            if self._node_status.get(node) != 'processed':
                # Mark as processed
                self._node_status[node] = 'processed'
                
                # CRITICAL: Increment processed predecessor count for all successors
                # This is necessary because we're marking the node as processed WITHOUT
                # going through the normal processing flow that would increment counts
                for successor in self._successor_map.get(node, []):
                    self._processed_predecessor_count[successor] += 1
                
                # Remove from active nodes if present
                if node in self._active_nodes:
                    self._active_nodes.remove(node)
                
                marked_count += 1
                
                if self.verbose:
                    print(f"Marked source node '{node.name}' as processed (has value: {node.value})")
        
        if self.verbose and marked_count > 0:
            print(f"\nMarked {marked_count} source nodes as processed")
            print(f"Remaining active nodes: {len(self._active_nodes)}")
            if self._active_nodes:
                print(f"Active: {[n.name for n in self._active_nodes]}")
        
        return marked_count
    
    def mark_container_nodes_as_processed(self):
        """
        Mark all ContainerNodes as 'processed' even if they have predecessors.
        
        This is specifically for MLP training where:
        - Weight ContainerNodes have initial random values
        - After backprop is added, they have dW gradient predecessors
        - But they need to provide initial values for the first forward pass
        
        This breaks the cycle: Forward pass needs weights → Backprop computes gradients → Weights update
        
        Call this AFTER adding backprop to the full graph, BEFORE training.
        
        Example usage:
            mlp = MLPGraphForwardProcessing(...)
            mlp.BuildMLP()
            backprop = BackpropGraphForwardProcessing(mlp, ...)
            backprop.BuildBackprop()
            
            full_graph = Graph()
            full_graph.AddNode(*mlp.nodes)
            full_graph.AddNode(*backprop.nodes)
            
            processor = GraphProcessor(full_graph)
            processor.mark_source_nodes_as_processed()  # Mark inputs, labels, LR
            processor.mark_container_nodes_as_processed()  # Mark weights with initial values
            processor.ForwardProcessing(iterations=...)
        
        Returns:
            int: Number of ContainerNodes marked as processed
        """
        from ComputationalGraphs.Nodes.ContainerNode import ContainerNode
        
        if not hasattr(self, '_forward_state_initialized') or not self._forward_state_initialized:
            # Initialize state first
            self._initialize_forward_state()
        
        # Initialize any nodes that were added after state initialization
        for node in self.graph.nodes:
            if node not in self._node_status:
                self._node_status[node] = 'unprocessed'
                self._processed_predecessor_count[node] = 0
        
        # Find all ContainerNodes
        container_nodes = [node for node in self.graph.nodes if isinstance(node, ContainerNode)]
        
        marked_count = 0
        for node in container_nodes:
            if self._node_status.get(node) != 'processed':
                # Mark as processed
                self._node_status[node] = 'processed'
                
                # CRITICAL: Increment processed predecessor count for all successors
                # This is necessary because we're marking the node as processed WITHOUT
                # going through the normal processing flow that would increment counts
                for successor in self._successor_map.get(node, []):
                    self._processed_predecessor_count[successor] += 1
                    if self.verbose:
                        print(f"  -> Incremented {successor.name}'s count to {self._processed_predecessor_count[successor]}/{self._predecessor_count[successor]}")
                
                # Remove from active nodes if present
                if node in self._active_nodes:
                    self._active_nodes.remove(node)
                
                marked_count += 1
                
                if self.verbose:
                    pred_count = len(node.predecessors)
                    print(f"Marked ContainerNode '{node.name}' as processed (value: {node.value}, predecessors: {pred_count})")
        
        if self.verbose and marked_count > 0:
            print(f"\nMarked {marked_count} ContainerNodes as processed")
            print(f"Remaining active nodes: {len(self._active_nodes)}")
            if self._active_nodes:
                print(f"Active: {[n.name for n in self._active_nodes[:5]]}...")
        
        return marked_count
    
    def has_active_nodes(self):
        """
        Check if there are any active nodes to process.
        
        Returns:
            bool: True if there are active nodes, False otherwise
        """
        if not hasattr(self, '_forward_state_initialized') or not self._forward_state_initialized:
            self._initialize_forward_state()
        return len(self._active_nodes) > 0
    
    def get_active_node_count(self):
        """
        Get the number of currently active nodes.
        
        Returns:
            int: Number of active nodes
        """
        if not hasattr(self, '_forward_state_initialized') or not self._forward_state_initialized:
            return 0
        return len(self._active_nodes)
    
    def ForwardProcessingComplete(self, stopping_nodes=None, stop_on_nth_hit=1,
                                  reactivate_nodes=None, reactivate_interval=None):
        """
        Execute forward processing until no active nodes remain or stopping condition met.
        Convenience method that runs complete forward+backward pass.
        
        Args:
            stopping_nodes: List of nodes that trigger termination (None = run until no active nodes)
            stop_on_nth_hit: Stop when any stopping node is processed this many times
            reactivate_nodes: List of nodes to reactivate periodically (e.g., input nodes)
            reactivate_interval: Reactivate nodes every N iterations (None = no reactivation)
        
        Returns:
            int: Total number of iterations executed
        """
        iterations_count = 0
        max_iterations = len(self.graph.nodes) * 3  # Safety limit
        
        while self.has_active_nodes() and iterations_count < max_iterations:
            active_count = self.ForwardProcessing(
                iterations=1, 
                stopping_nodes=stopping_nodes, 
                stop_on_nth_hit=stop_on_nth_hit,
                reactivate_nodes=reactivate_nodes,
                reactivate_interval=reactivate_interval
            )
            iterations_count += 1
            
            # Note: The old stopping-on-hit mechanism has been repurposed.
            # ForwardProcessing now uses graph-level `stopping_nodes` to
            # suppress successor candidation rather than terminating here.
        
        if self.verbose and iterations_count >= max_iterations:
            print(f"Warning: Reached maximum iteration limit ({max_iterations})")
        
        return iterations_count
    
    def _AllPredecessorsInSet(self, node, node_set):
        """
        Check if all predecessors of a node are in the given set.
        
        Args:
            node: The node to check
            node_set: Set of nodes to check against
        
        Returns:
            bool: True if all predecessors are in node_set, False otherwise
        """
        for predecessor in node.predecessors:
            if predecessor not in node_set:
                return False
        return True

    def __repr__(self):
        return f"GraphProcessor with {len(self.graph.nodes)} nodes at time={self.time}."


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

    def ForwardProcessing(self, iterations, starting_nodes=None):
        """
        Execute graph using forward processing - one timestep per iteration.
        
        In each iteration, we compute ONLY the nodes whose ALL predecessors 
        were computed in the PREVIOUS iteration. This advances the graph 
        one computational step at a time.
        
        OPTIMIZED: Only checks successors of previously computed nodes instead
        of scanning the entire graph.
        
        Args:
            iterations: Number of timesteps to advance the computation
            starting_nodes: List of nodes to activate in iteration 0. If None,
                          uses nodes with no predecessors (source nodes) and
                          ContainerNodes (for weights/parameters).
        """
        # Build successor map once for efficiency
        if not hasattr(self, 'successor_map') or self.successor_map is None:
            self.successor_map = self.graph.BuildSuccessorMap()
        
        # Build predecessor count map for faster readiness checking
        if not hasattr(self, 'predecessor_count_map'):
            self.predecessor_count_map = {node: len(node.predecessors) for node in self.graph.nodes}
        
        # Initialize: Determine which nodes are active at iteration 0
        if starting_nodes is not None:
            # User-specified starting nodes
            computed_in_previous_iteration = set(starting_nodes)
        else:
            # Auto-detect starting nodes
            computed_in_previous_iteration = set()
            for node in self.graph.nodes:
                if len(node.predecessors) == 0:
                    # True source nodes (inputs, constants, etc.)
                    computed_in_previous_iteration.add(node)
                elif node.__class__.__name__ == 'ContainerNode' and len(node.predecessors) > 0:
                    # ContainerNodes with predecessors = weights being updated
                    # They use their stored value in this iteration, then get updated for next
                    computed_in_previous_iteration.add(node)
            
            # Handle case where no starting nodes found
            if not computed_in_previous_iteration:
                if self.verbose:
                    print("WARNING: No starting nodes found. Using all nodes.")
                computed_in_previous_iteration = set(self.graph.nodes)
        
        # Track how many predecessors have been computed for each node
        # This allows O(1) readiness checking
        ready_predecessor_count = {node: 0 for node in self.graph.nodes}
        for node in computed_in_previous_iteration:
            for successor in self.successor_map.get(node, []):
                ready_predecessor_count[successor] += 1
        
        # Process each iteration (timestep)
        for iteration in range(iterations):
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"Forward Processing - Iteration {iteration + 1}/{iterations}")
                print(f"{'='*60}")
                print(f"Previously computed: {[n.name for n in computed_in_previous_iteration]}")
            
            # OPTIMIZATION: Only check successors of previously computed nodes
            # instead of scanning entire graph
            candidate_nodes = set()
            for node in computed_in_previous_iteration:
                for successor in self.successor_map.get(node, []):
                    candidate_nodes.add(successor)
            
            # Find nodes that are ready (all predecessors computed in previous iteration)
            active_nodes = []
            for node in candidate_nodes:
                # Check if ALL predecessors are ready
                if ready_predecessor_count[node] == self.predecessor_count_map[node]:
                    active_nodes.append(node)
            
            if self.verbose:
                print(f"Active nodes this iteration: {[n.name for n in active_nodes]}")
            
            # Process all active nodes in THIS iteration
            computed_in_this_iteration = set()
            for node in active_nodes:
                # Update inputs from predecessor nodes
                node.UpdateInputs()
                
                if self.verbose:
                    print(f"  {node.name}: inputs={node.inputs}")
                
                # Compute the node's value
                node.ProcessBatch()
                
                if self.verbose:
                    print(f"  {node.name}: computed value={node.value}")
                
                # Mark this node as computed in this iteration
                computed_in_this_iteration.add(node)
                
                # Update ready counts for successors
                for successor in self.successor_map.get(node, []):
                    ready_predecessor_count[successor] += 1
            
            if self.verbose:
                print(f"Computed {len(computed_in_this_iteration)} nodes this iteration")
            
            # Reset ready counts for nodes that were computed in previous iteration
            # They are no longer "active" for the next iteration
            for node in computed_in_previous_iteration:
                for successor in self.successor_map.get(node, []):
                    ready_predecessor_count[successor] -= 1
            
            # Prepare for next iteration: nodes computed THIS iteration become "previous"
            computed_in_previous_iteration = computed_in_this_iteration
            
            # Increment time counter
            self.time += 1
            
            # Optional visualization
            if self.visual:
                self.graph.DisplayGraph(fileName=f"forward_iteration_{iteration}")
    
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


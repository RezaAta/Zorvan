from concurrent.futures import ThreadPoolExecutor

class GraphProcessor:
    def __init__(self, graph, max_workers=4, verbose=True):
        self.graph = graph
        self.time = 0  # Initialize time for tracking iterations
        self.max_workers = max_workers  # Maximum number of threads for parallelism
        self.verbose = verbose  # Enable or disable printing

    def ComputeGraph(self, iterations=1):
        """
        Perform synchronous parallel computation for the graph over a number of iterations.
        Each node first updates its inputs, then performs operations in two separate parallel loops.
        """
        if self.verbose:
            print(f"Starting graph computation for {iterations} iterations...")

        if self.verbose:
            print("\n--- Time Step 0 ---")
            for node in self.graph.nodes:
                print(f"Node {node.name} has new value: {node.value}")

        for t in range(iterations):
            if self.verbose:
                print(f"\n--- Time Step {t+1} ---")

            # 1. First loop: Update the inputs for all nodes in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(node.UpdateInputs) for node in self.graph.nodes if not node.midCalculation]
                for future in futures:
                    future.result()  # Wait for all inputs to be copied before moving on

            # 2. Second loop: Process the batch for each node in parallel
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(node.ProcessBatch) for node in self.graph.nodes]
                for future in futures:
                    future.result()  # Wait for all nodes to finish processing

            # Print node values after processing
            if self.verbose:
                for node in self.graph.nodes:
                    print(f"Node {node.name} has new value: {node.value}")

            # Increment time after completing the time step
            self.time += 1
            if self.verbose:
                print(f"End of time step {t+1}. Time is now {self.time}.")
    
    def __repr__(self):
        return f"GraphProcessor with {len(self.graph.nodes)} nodes at time={self.time}."

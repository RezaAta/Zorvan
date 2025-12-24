from ComputationalGraphs.Nodes.Node import Node


class CompressedNode(Node):
    """
    A CompressedNode combines sequentially connected nodes into a single node.

    When processed, it executes its contained nodes in order (first to last).
    The compressed node's value is the value of the last node in the chain.

    Connection routing:
    - Predecessors: same as the first contained node
    - Successors: same as the last contained node

    This enables graph simplification while preserving computational semantics.
    """

    def __init__(self, name: str = "", nodes=None):
        """
        Initialize a CompressedNode.

        Args:
            name: The name of the compressed node (auto-generated as C1, C2)
            nodes: An ordered list of nodes to compress. Must be in chain order
                   (first node's output feeds into second node, etc.)
        """
        self.listOfNodes = list(nodes) if nodes else []
        # Set initial value from the last node if available
        self.value = self.listOfNodes[-1].value if self.listOfNodes else 0
        super().__init__(name)
        self.computationType = "complex"

    @property
    def first_node(self):
        """Return the first node in the chain (entry point for inputs)."""
        return self.listOfNodes[0] if self.listOfNodes else None

    @property
    def last_node(self):
        """Return the last node in the chain (exit point for outputs)."""
        return self.listOfNodes[-1] if self.listOfNodes else None

    # SetComputationStructure removed - unused by current serialization/UI flows.

    # UpdateComputationTime removed - was unused; re-add with tests if needed for profiling.
    def Operation(self, *inputs):
        """
        Execute all contained nodes sequentially in chain order.

        The first node receives inputs from the CompressedNode's predecessors.
        Each subsequent node receives inputs from its internal predecessors.
        The final value is taken from the last node.

        Args:
            *inputs: Inputs passed to the first node in the chain.

        Returns:
            The value of the last node after processing.
        """
        if not self.listOfNodes:
            return 0

        # Process each node in sequence
        for i, node in enumerate(self.listOfNodes):
            if i == 0:
                # First node: use the inputs passed to the CompressedNode
                # (which come from the CompressedNode's predecessors)
                if hasattr(node, "UpdateInputs"):
                    node.UpdateInputs()
                if hasattr(node, "Operation"):
                    if hasattr(node, "inputs"):
                        node.value = node.Operation(*node.inputs)
                    else:
                        node.value = node.Operation(*inputs)
            else:
                # Subsequent nodes: gather inputs from their predecessors
                # (which are inside the compressed node chain)
                if hasattr(node, "UpdateInputs"):
                    node.UpdateInputs()
                if hasattr(node, "Operation"):
                    if hasattr(node, "inputs"):
                        result = node.Operation(*node.inputs)
                    else:
                        result = node.Operation()
                    if result is not None:
                        node.value = result

        # The CompressedNode's value is the last node's value
        self.value = self.listOfNodes[-1].value
        return self.value

    def ProcessBatch(self, *inputs):
        """
        Process all contained nodes sequentially (not in parallel).

        Since nodes in a compressed chain depend on each other,
        they must be processed in order. Each node's UpdateInputs is called
        before its ProcessBatch to ensure proper input gathering.

        Note: Internal nodes are processed with forcedBatchProcessing=True
        temporarily to ensure all inputs are consumed in one pass.
        """
        if not self.listOfNodes:
            return

        for node in self.listOfNodes:
            # UpdateInputs gathers values from predecessors
            if hasattr(node, "UpdateInputs"):
                node.UpdateInputs()
            # ProcessBatch calls Operation with the gathered inputs
            # Temporarily enable forcedBatchProcessing to consume all inputs
            if hasattr(node, "ProcessBatch"):
                original_forced = getattr(node, "forcedBatchProcessing", False)
                node.forcedBatchProcessing = True
                node.ProcessBatch()
                node.forcedBatchProcessing = original_forced

        # Update the CompressedNode's value from the last node
        self.value = self.listOfNodes[-1].value if self.listOfNodes else 0

    def UpdateInputs(self):
        """
        Update inputs for the first node only.

        The first node gathers inputs from the CompressedNode's predecessors.
        Internal nodes will gather inputs from their internal predecessors
        during the Operation phase.
        """
        if self.listOfNodes and hasattr(self.listOfNodes[0], "UpdateInputs"):
            # First node uses CompressedNode's predecessors as input source
            # Internal predecessor links are preserved, so just update it
            self.listOfNodes[0].UpdateInputs()

        # Also collect inputs at the CompressedNode level
        self.inputs = [
            pred.value for pred in self.predecessors if hasattr(pred, "value")
        ]

    def extend_front(self, node):
        """
        Add a node to the front of the chain (new entry point).

        Args:
            node: The node to add at the beginning.
        """
        self.listOfNodes.insert(0, node)

    def extend_back(self, node):
        """
        Add a node to the back of the chain (new exit point).

        Args:
            node: The node to add at the end.
        """
        self.listOfNodes.append(node)

    def pop_front(self):
        """
        Remove and return the first node from the chain.

        Returns:
            The removed node, or None if the chain is empty.
        """
        if self.listOfNodes:
            return self.listOfNodes.pop(0)
        return None

    def pop_back(self):
        """
        Remove and return the last node from the chain.

        Returns:
            The removed node, or None if the chain is empty.
        """
        if self.listOfNodes:
            return self.listOfNodes.pop()
        return None

    def get_internal_nodes(self):
        """
        Return a copy of the list of internal nodes.

        Returns:
            A new list containing all nodes in the chain.
        """
        return list(self.listOfNodes)

    def __len__(self):
        """Return the number of nodes in the compressed chain."""
        return len(self.listOfNodes)

    def __repr__(self):
        node_names = [getattr(n, "name", str(n)) for n in self.listOfNodes]
        return f"CompressedNode({self.name}, chain=[{' -> '.join(node_names)}])"

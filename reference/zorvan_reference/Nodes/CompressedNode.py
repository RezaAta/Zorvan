from zorvan_reference.Nodes.computation_type import ComputationType
from zorvan_reference.Nodes.Node import Node


class CompressedNode(Node):
    """
    A CompressedNode combines sequentially connected nodes into a single node.

    Under the graph processors (UpdateInputs + ProcessBatch per tick), a
    compressed chain behaves exactly like the uncompressed nodes: each internal
    node advances one tick at a time from the tick snapshot. Calling
    Operation() directly instead evaluates the whole chain in one shot (a
    "merged" evaluation), which does NOT preserve per-tick timing.
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
        self.nodes = list(nodes) if nodes else []
        # Set initial value from the last node if available
        self.value = self.nodes[-1].value if self.nodes else 0
        super().__init__(name)
        self.computationType = ComputationType.COMPLEX

    @property
    def first_node(self):
        """Return the first node in the chain (entry point for inputs)."""
        return self.nodes[0] if self.nodes else None

    @property
    def last_node(self):
        """Return the last node in the chain (exit point for outputs)."""
        return self.nodes[-1] if self.nodes else None

    # Public attribute 'nodes' stores internal node list (list)

    # Note: assigning to 'nodes' should keep 'value' consistent with last inner node.

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
        if not self.nodes:
            return 0

        # Process each node in sequence
        for i, node in enumerate(self.nodes):
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
        self.value = self.nodes[-1].value
        return self.value

    def ProcessBatch(self, *inputs):
        """
        Phase 2 of a processing tick: process every internal node.

        Inputs were already captured from the tick snapshot in UpdateInputs()
        (Phase 1), so internal nodes must NOT re-read their inputs here.
        This keeps the chain's per-tick latency identical to the uncompressed
        graph (compression is a view, not a change of semantics), and makes
        the result independent of processing order.
        """
        if not self.nodes:
            return

        for node in self.nodes:
            if hasattr(node, "ProcessBatch"):
                node.ProcessBatch()

        # Update the CompressedNode's value from the last node
        self.value = self.nodes[-1].value

    def UpdateInputs(self):
        """
        Phase 1 of a processing tick: snapshot inputs for every internal node.

        The first node reads the chain's external predecessors; each later node
        reads the previous node's value from the *previous* tick, exactly as it
        would in the uncompressed graph. Nodes that are mid-calculation are
        skipped, mirroring the processors' rule for top-level nodes.
        """
        for node in self.nodes:
            if getattr(node, "midCalculation", False):
                continue
            if hasattr(node, "UpdateInputs"):
                node.UpdateInputs()

        # Also collect inputs at the CompressedNode level
        self.inputs = [
            pred.value for pred in self.predecessors if hasattr(pred, "value")
        ]

    def pop_front(self):
        """
        Remove and return the first node from the chain.

        Returns:
            The removed node, or None if the chain is empty.
        """
        if self.nodes:
            return self.nodes.pop(0)
        return None

    def pop_back(self):
        """
        Remove and return the last node from the chain.

        Returns:
            The removed node, or None if the chain is empty.
        """
        if self.nodes:
            return self.nodes.pop()
        return None

    def get_internal_nodes(self):
        """
        Return a copy of the list of internal nodes.

        Returns:
            A new list containing all nodes in the chain.
        """
        return list(self.nodes)

    def __len__(self):
        """Return the number of nodes in the compressed chain."""
        return len(self.nodes)

    def __repr__(self):
        node_names = [getattr(n, "name", str(n)) for n in self.nodes]
        return f"CompressedNode({self.name}, chain=[{' -> '.join(node_names)}])"

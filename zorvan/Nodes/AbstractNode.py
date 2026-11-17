from concurrent.futures import ThreadPoolExecutor

from zorvan.Nodes.computation_type import ComputationType
from zorvan.Nodes.Node import Node


class AbstractNode(Node):
    """
    An AbstractNode groups multiple disjoint (unconnected) nodes into a single unit.

    Unlike CompressedNode which chains sequential nodes, AbstractNode represents
    a set of parallel nodes that share the same predecessors and successors.
    All internal nodes execute in parallel and receive the same inputs.

    Connection routing:
    - Predecessors: External predecessors are shared by all internal nodes
    - Successors: External successors connect from the AbstractNode (Cartesian product)

    The value of an AbstractNode is a list of values from all contained nodes.
    This enables graph topology simplification by treating parallel nodes as a set.
    """

    def __init__(self, name: str = "", nodes=None):
        """
        Initialize an AbstractNode.

        Args:
            name: The name of the abstract node (auto-generated as A1, A2, etc.)
            nodes: A list of disjoint nodes to abstract. These nodes must share
                   the same predecessors and successors, and not be connected to each other.
        """
        # Use list for stable ordering (serialization, display) while
        # enforcing disjointness via validation at abstraction time
        self.nodes = list(nodes) if nodes else []

        # Initialize before calling super().__init__ since it may access predecessors
        super().__init__(name)

        # External predecessors will be set by Graph.abstract_nodes()
        # Do NOT set internal nodes as predecessors (that was a bug)
        # Standardize on 'computationType' (used by BasicNode/CompressedNode)
        self.computationType = ComputationType.COMPLEX

        # Value is a list of all internal node values
        self.value = [node.value for node in self.nodes]

    # Public attribute 'nodes' stores internal node list (list)

    # SetComputationStructure removed - was unused. Reintroduce only if serialization/UI needs it.

    def UpdateValues(self):
        """Update the AbstractNode's value list from all internal nodes."""
        for node in self.nodes:
            if isinstance(node, AbstractNode):
                node.UpdateValues()
        self.value = [node.value for node in self.nodes]

    # UpdateComputationTime removed - no external callers. Reintroduce with tests if profiling is required.

    def Operation(self, *inputs):
        """
        Execute all contained nodes in parallel.

        All internal nodes receive the same inputs (from the AbstractNode's predecessors).
        The result is a list of values from all internal nodes.

        Args:
            *inputs: Inputs passed to ALL internal nodes.

        Returns:
            A list of values from all internal nodes.
        """
        if not self.nodes:
            return []

        # Process each node in parallel
        with ThreadPoolExecutor() as executor:

            def process_node(node):
                if hasattr(node, "UpdateInputs"):
                    node.UpdateInputs()
                if hasattr(node, "Operation"):
                    if hasattr(node, "inputs") and node.inputs:
                        result = node.Operation(*node.inputs)
                    else:
                        result = node.Operation(*inputs)
                    if result is not None:
                        node.value = result
                return node.value

            futures = [executor.submit(process_node, node) for node in self.nodes]
            results = [future.result() for future in futures]

        self.value = results
        return self.value

    def ProcessBatch(self, *inputs):
        """
        Phase 2 of a processing tick: process every internal node.

        Inputs were already captured from the tick snapshot in UpdateInputs()
        (Phase 1); internal nodes must NOT re-read them here, otherwise they
        would see values already updated in this tick and the result would
        depend on processing order. Internal nodes are processed sequentially:
        they are independent, so order does not matter, and avoiding a thread
        pool per node per tick keeps runs deterministic and cheaper.
        """
        if not self.nodes:
            return

        for node in self.nodes:
            if hasattr(node, "ProcessBatch"):
                node.ProcessBatch()

        self.value = [node.value for node in self.nodes]

    def UpdateInputs(self):
        """
        Phase 1 of a processing tick: snapshot inputs for every internal node.

        Each internal node gathers from its own predecessors (the shared
        external predecessors). Nodes that are mid-calculation are skipped,
        mirroring the processors' rule for top-level nodes.
        """
        # Collect inputs at the AbstractNode level
        self.inputs = [
            pred.value for pred in self.predecessors if hasattr(pred, "value")
        ]

        for node in self.nodes:
            if getattr(node, "midCalculation", False):
                continue
            if hasattr(node, "UpdateInputs"):
                node.UpdateInputs()

    # --- Methods for managing internal nodes ---

    # Instance-level mutation helpers (`extend`, `remove`, `expand`) were
    # removed because node list management should be performed by Graph-level
    # APIs to ensure adjacency/validation invariants. Use `get_internal_nodes`
    # for read-only access to the internal nodes.

    def get_internal_nodes(self):
        """
        Return a copy of the list of internal nodes.

        Returns:
            A new list containing all nodes in the abstraction.
        """
        return list(self.nodes)

    def __len__(self):
        """Return the number of nodes in the abstraction."""
        return len(self.nodes)

    def __repr__(self):
        node_names = [getattr(n, "name", str(n)) for n in self.nodes]
        return f"AbstractNode({self.name}, nodes=[{', '.join(node_names)}])"

    def __contains__(self, node):
        """Check if a node is contained in this AbstractNode."""
        return node in self.nodes

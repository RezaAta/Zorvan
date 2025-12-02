from concurrent.futures import ThreadPoolExecutor

from ComputationalGraphs.Nodes.Node import Node


class AbstractNode(Node):

    def __init__(self, name: str = "", nodes=None):
        if nodes:
            self.nodes = nodes
            self.predecessors = [node for node in nodes]
        else:
            self.nodes = set()  # Set of nodes

        super().__init__(name)
        self.computationalType = "complex"  # Computational type is complex
        self.value = [node.value for node in self.nodes]

    def SetComputationStructure(self):
        """
        Generate a string that represents the computation structure of the AbstractNode.
        The structure is represented as (node1, node2, ...).
        """
        if self.nodes:
            node_ids = [node.id for node in self.nodes]
            self.computationalStructure = f"({', '.join(node_ids)})"
        else:
            self.computationalStructure = self.id

    def UpdateValues(self):
        for node in self.nodes:
            if isinstance(node, AbstractNode):
                node.UpdateValues()
            self.value = [node.value for node in self.nodes]

    def UpdateComputationTime(self):
        """
        Update the computation time of the AbstractNode.
        The computation time is set to the max computation time of all its nodes.
        """
        if self.nodes:
            self.computationTime = max(node.computationTime for node in self.nodes)
        else:
            self.computationTime = 1

    def Operation(self, *inputs):
        pass

    def ProcessBatch(self, *inputs):
        """
        Perform an operation on all nodes in parallel. In this example, we will assume
        that each node performs its own operation independently.
        """
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(node.ProcessBatch) for node in self.nodes]
            # Wait for all nodes to complete their operations in parallel
            for future in futures:
                future.result()  # Retrieve the result of each operation (if needed)

    def UpdateInputs(self):
        """
        Update the inputs array with the values from all nodes in the set.
        """
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(node.UpdateInputs) for node in self.nodes]
            # Wait for all nodes to complete their operations in parallel
            for future in futures:
                future.result()  # Retrieve the result of each operation (if needed)

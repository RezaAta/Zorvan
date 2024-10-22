from Node import Node
from concurrent.futures import ThreadPoolExecutor

class AbstractNode(Node):
    def __init__(self, name: str = "", nodes=None):
        """
        Initialize an AbstractNode with a set of nodes.
        """
        super().__init__(name)
        self.nodes = nodes if nodes else set()  # Set of nodes
        self.computationalType = "complex"  # Computational type is complex
        self.UpdateComputationTime()
        self.GenerateComputationStructure()
        if self.name == "":
            self.name = id

    def AddNode(self, node):
        """
        Add a node to the abstraction set.
        """
        self.nodes.add(node)
        self.UpdateComputationTime()
        self.GenerateComputaionStructure()

    def RemoveNode(self, node):
        """
        Remove a node from the abstraction set.
        """
        if node in self.nodes:
            self.nodes.remove(node)
        self.UpdateComputationTime()
        self.GenerateComputaionStructure()

    def GenerateComputationStructure(self):
        """
        Generate a string that represents the computation structure of the AbstractNode.
        The structure is represented as (node1, node2, ...).
        """
        node_ids = [node.id for node in self.nodes]
        return f"({', '.join(node_ids)})"

    def UpdateComputationTime(self):
        """
        Update the computation time of the AbstractNode.
        The computation time is set to the max computation time of all its nodes.
        """
        if self.nodes:
            self.computationTime = max(node.computationTime for node in self.nodes)
        else:
            self.computationTime = 0

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


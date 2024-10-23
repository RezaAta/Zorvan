from Node import Node
from concurrent.futures import ThreadPoolExecutor


# CompressedNode: A Node with a list of nodes
class CompressedNode(Node):
    def __init__(self, name: str = "", nodes=None):
        self.listOfNodes = nodes if nodes else []
        self.value = self.listOfNodes[-1].value if self.listOfNodes else 0
        super().__init__(name)
        self.computationType = 'complex'

    def SetComputationStructure(self):
        """
        Generate a string that represents the computation structure of the CompressedNode.
        The structure is represented as the concatenation of all node names in the list.
        """
        if self.listOfNodes:
            self.computationStructure = ''.join(node.id for node in self.listOfNodes)
        else:
            self.computationStructure = self.id  # If no nodes are present, return an empty string

    def UpdateComputationTime(self):
        """
        Update the computation time of the AbstractNode.
        The computation time is set to the sum computation time of all its nodes.
        """
        if self.listOfNodes:
            self.computationTime = sum(node.computationTime for node in self.listOfNodes)
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
            futures = [executor.submit(node.ProcessBatch) for node in self.listOfNodes]
            # Wait for all nodes to complete their operations in parallel
            for future in futures:
                future.result()  # Retrieve the result of each operation (if needed)

    def UpdateInputs(self):
        """
        Update the inputs array with the values from all nodes in the set.
        """
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(node.UpdateInputs) for node in self.listOfNodes]
            # Wait for all nodes to complete their operations in parallel
            for future in futures:
                future.result()  # Retrieve the result of each operation (if needed)
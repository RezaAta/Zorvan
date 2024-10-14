from abc import ABC, abstractmethod

class Node(ABC):
    def __init__(self, name, topologicalType="isolated", computationTime=1, value=0):
        self.name = name
        self.value = value
        self.predecessors = []  # List to store predecessor nodes
        self.topologicalType = topologicalType
        self.computationTime = computationTime
        self.computationStructure = name  # Default to the node's name
    
    @abstractmethod
    def operation(self):
        """Abstract method for performing the node's computation."""
        pass
    
    def add_pre_node(self, pre_node):
        """Add a predecessor node."""
        self.predecessors.append(pre_node)
    
    def remove_pre_node(self, pre_node=None):
        """Remove a predecessor node. If no node is specified, remove the last added one."""
        if pre_node:
            self.predecessors.remove(pre_node)
        elif self.predecessors:
            self.predecessors.pop()

    def __repr__(self):
        return f"Node(name={self.name}, value={self.value}, type={self.topologicalType}, predecessors={len(self.predecessors)})"


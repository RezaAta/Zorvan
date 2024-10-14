from .Node import Node

class AdditionNode(Node):
    def __init__(self, name, topologicalType="isolated", computationTime=1, value=0):
        super().__init__(name, topologicalType, computationTime, value)
    
    def operation(self):
        """Perform addition of predecessor values."""
        return sum(node.value for node in self.predecessors)
    

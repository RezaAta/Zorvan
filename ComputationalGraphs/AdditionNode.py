from .Node import Node

class AdditionNode(Node):
    def __init__(self, name, value=0):
        super().__init__(name, value)
    
    def operation(self):
        """Perform addition of predecessor values."""
        return sum(node.value for node in self.predecessors)
    

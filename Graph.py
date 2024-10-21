from BasicNode import BasicNode  # Import the abstract BasicNode class

class Graph:
    def __init__(self):
        self.nodes = []  # List to hold nodes
        self.adjacencyMatrix = []  # Adjacency matrix for node connections
        self.nameToNodeDictionary = {}  # Map node names to node objects

    def AddNewNode(self, name, nodeType, value=0):
        """Create a new node of a specific type and add it to the graph."""
        if nodeType == "Addition":
            from AdditionNode import AdditionNode  # Import AdditionNode only when needed
            new_node = AdditionNode(name)
        else:
            raise ValueError("Unsupported node type: {nodeType}")
        
        # Add the new node to the graph
        self.AddNode(new_node)

    def AddNode(self, *nodeObjects):
        """Add an existing node object to the graph."""
        for nodeObject in nodeObjects:
            self.nodes.append(nodeObject)
            self.nameToNodeDictionary[nodeObject.name] = nodeObject

            # Extend the adjacency matrix for the new node
            size = len(self.adjacencyMatrix)
            for row in self.adjacencyMatrix:
                row.append(0)  # Extend existing rows for the new node column
            self.adjacencyMatrix.append([0] * (size + 1))  # Add new row for the new node

            # Update adjacency matrix for the new node's predecessors
            node_index = self.nodes.index(nodeObject)
            for predecessor in nodeObject.predecessors:
                if predecessor in self.nodes:
                    pred_index = self.nodes.index(predecessor)
                    self.adjacencyMatrix[pred_index][node_index] = 1  # Connection from predecessor to new node

    def ConnectPreNode(self, node, *preNodes):
        for preNode in preNodes:
            """Manually connect a predecessor to a node and update the adjacency matrix."""
            node.AddPreNode(preNode)  # Add the predecessor to the node's list

            # Update adjacency matrix for the new connection
            node_index = self.nodes.index(node)
            preNode_index = self.nodes.index(preNode)
            self.adjacencyMatrix[preNode_index][node_index] = 1  # Connection from predecessor to node

    def UpdateAdjacencyMatrix(self):
        """Rebuild the adjacency matrix by iterating over all nodes and their connections."""
        size = len(self.nodes)
        self.adjacencyMatrix = [[0] * size for _ in range(size)]  # Reset matrix

        for i, node in enumerate(self.nodes):
            for predecessor in node.predecessors:
                if predecessor in self.nodes:
                    pred_index = self.nodes.index(predecessor)
                    self.adjacencyMatrix[pred_index][i] = 1  # Mark the connection

    def RemoveNode(self, identifier):
        """Remove a node from the graph by object, name, or index."""
        # Identify the node to remove based on its type (index, name, or object)
        if isinstance(identifier, int):
            node_to_remove = self.nodes[identifier]
        elif isinstance(identifier, str):
            node_to_remove = self.nameToNodeDictionary.get(identifier)
            if node_to_remove is None:
                raise ValueError(f"Node with name '{identifier}' not found.")
        else:
            node_to_remove = identifier

        # Remove the node from the graph
        if node_to_remove in self.nodes:
            index = self.nodes.index(node_to_remove)
            self.nodes.remove(node_to_remove)

            # Remove from the adjacency matrix
            del self.adjacencyMatrix[index]  # Remove row
            for row in self.adjacencyMatrix:
                del row[index]  # Remove column

            # Remove from name-to-node mapping
            del self.nameToNodeDictionary[node_to_remove.name]
        else:
            raise ValueError("Node not found in the graph")

    def __repr__(self):
        return f"Graph with {len(self.nodes)} nodes."

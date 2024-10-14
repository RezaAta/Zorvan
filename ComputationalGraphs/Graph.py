# Graph.py
from .Node import Node  # Import the abstract Node class

class Graph:
    def __init__(self):
        self.nodes = []  # List to hold nodes
        self.adjacencyMatrix = []  # Adjacency matrix for connections
        self.nameToNodeDictionary = {}  # Dictionary to map names to nodes

    def AddNewNode(self, name, nodeType, value=0):
        """Create a new node of a specific type and add it to the graph."""
        if nodeType == "Addition":
            from .AdditionNode import AdditionNode  # Import AdditionNode
            new_node = AdditionNode(name, value)
        else:
            raise ValueError("Unsupported node type")
        
        self.AddNode(new_node)  # Add the newly created node to the graph

    def AddNode(self, nodeObj):
        """Add an existing node object to the graph."""
        self.nodes.append(nodeObj)
        self.nameToNodeDictionary[nodeObj.name] = nodeObj

        # Extend the adjacency matrix for the new node
        size = len(self.adjacencyMatrix)
        for row in self.adjacencyMatrix:
            row.append(0)  # Extend existing rows
        self.adjacencyMatrix.append([0] * (size + 1))  # Add new row for the new node

        # Update the adjacency matrix for the new node's connections (predecessors)
        node_index = self.nodes.index(nodeObj)
        for predecessor in nodeObj.predecessors:
            if predecessor in self.nodes:
                pred_index = self.nodes.index(predecessor)
                self.adjacencyMatrix[pred_index][node_index] = 1  # Connection from predecessor to new node

    def connect_pre_node(self, node, pre_node):
        """
        Manually connect a predecessor to a node and update the adjacency matrix.
        """
        node.add_pre_node(pre_node)  # Add the predecessor to the node

        # Update the adjacency matrix for the new connection
        node_index = self.nodes.index(node)
        pre_node_index = self.nodes.index(pre_node)
        self.adjacencyMatrix[pre_node_index][node_index] = 1  # Mark the connection

    def update_adjacency_matrix(self):
        """
        Manually update the entire adjacency matrix by iterating over all nodes
        and their connections.
        """
        # Reset the adjacency matrix
        size = len(self.nodes)
        self.adjacencyMatrix = [[0] * size for _ in range(size)]

        # Rebuild the adjacency matrix based on the current connections
        for i, node in enumerate(self.nodes):
            for predecessor in node.predecessors:
                if predecessor in self.nodes:
                    pred_index = self.nodes.index(predecessor)
                    self.adjacencyMatrix[pred_index][i] = 1  # Connection from predecessor to node

    def RemoveNode(self, identifier):
        """Remove a node from the graph by object, name, or index."""
        if isinstance(identifier, int):  # If an index is provided
            node_to_remove = self.nodes[identifier]
        elif isinstance(identifier, str):  # If a name is provided
            node_to_remove = self.nameToNodeDictionary.get(identifier)
            if node_to_remove is None:
                raise ValueError("Node not found")
        else:  # If an object is provided
            node_to_remove = identifier

        # Remove the node from the graph
        if node_to_remove in self.nodes:
            index = self.nodes.index(node_to_remove)
            self.nodes.remove(node_to_remove)
            del self.adjacencyMatrix[index]  # Remove the row from the adjacency matrix
            for row in self.adjacencyMatrix:
                del row[index]  # Remove the column from the adjacency matrix
            del self.nameToNodeDictionary[node_to_remove.name]  # Remove from the dictionary
        else:
            raise ValueError("Node not found in the graph")

    def __repr__(self):
        return f"Graph with {len(self.nodes)} nodes."

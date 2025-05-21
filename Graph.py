from Node import Node
from BasicNode import BasicNode  # Import the abstract BasicNode class
from AbstractNode import AbstractNode
from CompressedNode import CompressedNode
from graphviz import Digraph

class Graph:
    def __init__(self):
        self.nodes = []  # List to hold nodes
        self.adjacencyMatrix = []  # Adjacency matrix for node connections
        self.idToNodeDictionary = {}  # Map node ids to node objects
        
        # Counters for the first naming convention
        self.abstract_counter = 1
        self.compressed_counter = 1
        self.basic_counter = 0  # Using alphabet positions for basic nodes
        self.basic_suffix_counter = 1  # Used when a-z are all used up

    def GenerateIdForNode(self,node):
        """
        Generate a new id for a node based on the type and naming convention.
        """
        if isinstance(node,AbstractNode):
            id = f"A{self.abstract_counter}"
            self.abstract_counter += 1
        elif isinstance(node,CompressedNode):
            id = f"C{self.compressed_counter}"
            self.compressed_counter += 1
        elif isinstance(node,BasicNode):
            # Generate a letter for basic nodes
            if self.basic_counter < 26:  # 'a' to 'z'
                id = chr(97 + self.basic_counter)  # ASCII 'a' = 97
                self.basic_counter += 1
            else:
                # If 'a' to 'z' are used, use suffixes like 'a1', 'b1', etc.
                base_letter = chr(97 + (self.basic_counter % 26))  # Cycle through 'a' to 'z'
                id = f"{base_letter}{self.basic_suffix_counter}"
                self.basic_counter += 1
                if self.basic_counter % 26 == 0:  # Every full cycle increases the suffix
                    self.basic_suffix_counter += 1
        else:
            raise ValueError("Unknown node type. Must be 'abstract', 'compressed', or 'basic'.")

        # Ensure uniqueness by appending a counter if the id is already used
        original_id = id
        counter = 1
        while id in self.idToNodeDictionary:
            id = f"{original_id}_{counter}"
            counter += 1

        return id

    def AddNode(self, *nodeObjects):
        """Add an existing node object to the graph."""
        for nodeObject in nodeObjects:
            nodeObject.id = self.GenerateIdForNode(nodeObject)  # Generate a unique id for the node
            self.nodes.append(nodeObject)
            self.idToNodeDictionary[nodeObject.id] = nodeObject

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

    def RemoveNode(self, *identifiers):
        """Remove nodes from the graph by object, id, or index."""
        for identifier in identifiers:
            # identify the node to remove based on its type (index, id, or object)
            nodeToRemove = self.__IdentifyNode(identifier)

            if nodeToRemove in self.nodes:
                # Get the index of the node to be removed
                index = self.nodes.index(nodeToRemove)

                # Update the adjacency matrix: remove connections to the node
                self.__RemoveNodeConnectionsInMatrix(nodeToRemove, index)

                # Remove the node from the adjacency matrix
                self.__RemoveNodeFromAdjacencyMatrix(index)

                # Remove the node from the graph and the id-to-node dictionary
                self.nodes.remove(nodeToRemove)
                del self.idToNodeDictionary[nodeToRemove.id]
            else:
                raise ValueError(f"Node '{nodeToRemove}' not found in the graph.")


    def __repr__(self):
        return f"Graph with {len(self.nodes)} nodes."
    
    def AbstractNodes(self, nodes):
        """
        Create an AbstractNode from a set of nodes.
        """
        abstract = AbstractNode("", nodes)
        self.ReplaceNode(abstract, *nodes)
        return abstract

    def ReplaceNode(self, newNode, *oldNode):
        self.AddNode(newNode)
        self.ReplicateConnections(newNode,*oldNode)
        self.RemoveNode(*oldNode)
        self.UpdateAdjacencyMatrix()

    def ReplicateConnections(self,newNode: Node,*oldNodes: Node):
        """
        Replicate the connections of old nodes in the graph to the new node.
        - newNode: The node that will take over connections from old nodes.
        - oldNodes: One or more old nodes whose connections are transferred to the new node.
        """
        for oldNode in oldNodes:
            oldNodeIndex = self.nodes.index(oldNode)
            # Replicate outgoing connections (connections from the old node to others)
            for j in range(len(self.adjacencyMatrix[oldNodeIndex])):
                if self.adjacencyMatrix[oldNodeIndex][j] == 1:  # If old node connects to another node
                    self.nodes[j].AddPreNode(newNode)
            

    def CompressNodes(self, nodes):
        """
        Create a CompressedNode from a set of nodes.
        """
        compressed = CompressedNode("", nodes)
        self.RemoveNode(*nodes)
        self.AddNode(compressed)
        return compressed
    
    def DisplayGraph(self, fileName = "ComputationalGraph"):
        """Visualize the MLP graph in a left-to-right layout using Graphviz."""
        dot = Digraph(format='svg')
        dot.attr(rankdir='LR')  # Set the layout to be left-to-right
        for node in self.nodes:
            dot.node(node.name, label=f"{node.name}\n({type(node).__name__})\n{node.value}")
        for i, row in enumerate(self.adjacencyMatrix):
            for j, connection in enumerate(row):
                if connection == 1:
                    dot.edge(self.nodes[i].name, self.nodes[j].name)
        dot.render(filename = fileName, view=True)

    def __RemoveNodeFromAdjacencyMatrix(self, index):
        del self.adjacencyMatrix[index]
        for row in self.adjacencyMatrix:
            del row[index]

    def __RemoveNodeConnectionsInMatrix(self, nodeToRemove, index):
        for i in range(len(self.adjacencyMatrix)):
            # Remove node from predecessors
            if self.adjacencyMatrix[index][i] == 1:
                self.nodes[i].predecessors.remove(nodeToRemove)

    def __IdentifyNode(self, identifier):
        if isinstance(identifier, int):
            node = self.nodes[identifier]
        elif isinstance(identifier, str):
            node = self.idToNodeDictionary.get(identifier)
            if node is None:
                raise ValueError(f"Node with id '{identifier}' not found.")
        else:
            node = identifier
        return node
    

    def ResetNodeValues(self):
        for node in self.nodes:
            node.ResetValue()


    # any node that old nodes are in its pred list
    # put the new abstract node in its pred list
    
from graphviz import Digraph

from ComputationalGraphs.Nodes.AbstractNode import AbstractNode
from ComputationalGraphs.Nodes.BasicNode import (  # Import the abstract BasicNode class
    BasicNode,
)
from ComputationalGraphs.Nodes.CompressedNode import CompressedNode
from ComputationalGraphs.Nodes.Node import Node


class Graph:
    def __init__(self):
        self.nodes = []  # List to hold nodes
        self.adjacencyMatrix = []  # Adjacency matrix for node connections
        self.idToNodeDictionary = {}  # Map node ids to node objects
        self.starting_nodes = []  # Entry points for graph execution (e.g., input nodes)
        # Optional manual node processing sequence: list of iterables of Node identifiers
        # Each item in the list represents the set of nodes to process at a single iteration.
        # Accepts Node objects, node ids (strings), or node indices (ints).
        self.manual_processing_sequence = None

        # Counters for the first naming convention
        self.abstract_counter = 1
        self.compressed_counter = 1
        self.basic_counter = 0  # Using alphabet positions for basic nodes
        self.basic_suffix_counter = 1  # Used when a-z are all used up

    def GenerateIdForNode(self, node):
        """
        Generate a new id for a node based on the type and naming convention.
        """
        if isinstance(node, AbstractNode):
            id = f"A{self.abstract_counter}"
            self.abstract_counter += 1
        elif isinstance(node, CompressedNode):
            id = f"C{self.compressed_counter}"
            self.compressed_counter += 1
        elif isinstance(node, BasicNode):
            # Generate a letter for basic nodes
            if self.basic_counter < 26:  # 'a' to 'z'
                id = chr(97 + self.basic_counter)  # ASCII 'a' = 97
                self.basic_counter += 1
            else:
                # If 'a' to 'z' are used, use suffixes like 'a1', 'b1', etc.
                base_letter = chr(
                    97 + (self.basic_counter % 26)
                )  # Cycle through 'a' to 'z'
                id = f"{base_letter}{self.basic_suffix_counter}"
                self.basic_counter += 1
                if (
                    self.basic_counter % 26 == 0
                ):  # Every full cycle increases the suffix
                    self.basic_suffix_counter += 1
        else:
            raise ValueError(
                "Unknown node type. Must be 'abstract', 'compressed', or 'basic'."
            )

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
            nodeObject.id = self.GenerateIdForNode(
                nodeObject
            )  # Generate a unique id for the node
            self.nodes.append(nodeObject)
            self.idToNodeDictionary[nodeObject.id] = nodeObject

            # Extend the adjacency matrix for the new node
            size = len(self.adjacencyMatrix)
            for row in self.adjacencyMatrix:
                row.append(0)  # Extend existing rows for the new node column
            self.adjacencyMatrix.append(
                [0] * (size + 1)
            )  # Add new row for the new node

            # Update adjacency matrix for the new node's predecessors
            node_index = self.nodes.index(nodeObject)
            for predecessor in nodeObject.predecessors:
                if predecessor in self.nodes:
                    pred_index = self.nodes.index(predecessor)
                    self.adjacencyMatrix[pred_index][
                        node_index
                    ] = 1  # Connection from predecessor to new node

    def ConnectPreNode(self, node, *preNodes):
        for preNode in preNodes:
            """Manually connect a predecessor to a node and update the adjacency matrix."""
            node.AddPreNode(preNode)  # Add the predecessor to the node's list

            # Update adjacency matrix for the new connection
            node_index = self.nodes.index(node)
            preNode_index = self.nodes.index(preNode)
            self.adjacencyMatrix[preNode_index][
                node_index
            ] = 1  # Connection from predecessor to node

    def DisconnectPreNode(self, node, *preNodes):
        """Disconnect predecessor(s) from a node and update the adjacency matrix."""
        if node not in self.nodes:
            return
        for preNode in preNodes:
            # If the exact node object is present, remove directly
            if preNode in node.predecessors:
                try:
                    node.predecessors.remove(preNode)
                    # Debug output to help with synchronization issues
                    try:
                        print(
                            f"Graph: removed predecessor {getattr(preNode, 'name', str(preNode))} from {getattr(node, 'name', str(node))}"
                        )
                    except Exception:
                        pass
                except Exception:
                    pass
                continue

            # If not identical object, try to match on id or name (common in GUI replacements)
            # Accept string identifiers for convenience
            candidates = list(node.predecessors)
            matched = None
            if isinstance(preNode, str):
                for cand in candidates:
                    if hasattr(cand, "name") and cand.name == preNode:
                        matched = cand
                        break
                    if hasattr(cand, "id") and cand.id == preNode:
                        matched = cand
                        break
            else:
                # preNode is a Node (or similar) but a different object instance - try matching by id/name
                try:
                    pid = getattr(preNode, "id", None)
                    pname = getattr(preNode, "name", None)
                except Exception:
                    pid = None
                    pname = None
                for cand in candidates:
                    if pid is not None and getattr(cand, "id", None) == pid:
                        matched = cand
                        break
                    if pname is not None and getattr(cand, "name", None) == pname:
                        matched = cand
                        break

            if matched is not None and matched in node.predecessors:
                try:
                    node.predecessors.remove(matched)
                    try:
                        print(
                            f"Graph: removed predecessor {getattr(matched, 'name', str(matched))} from {getattr(node, 'name', str(node))} (matched)"
                        )
                    except Exception:
                        pass
                except Exception:
                    pass
        # Rebuild the adjacency matrix to reflect changes
        self.UpdateAdjacencyMatrix()

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
        # Add new node; transfer attributes and connections from oldNode
        self.AddNode(newNode)
        # Transfer attributes where applicable
        try:
            self.TransferNodeAttributes(oldNode[0], newNode)
        except Exception:
            # If there's an issue, we still proceed
            pass
        self.ReplicateConnections(newNode, *oldNode)
        # If old node was in starting_nodes, replace it with newNode
        for i, sn in enumerate(list(self.starting_nodes)):
            if sn in oldNode:
                try:
                    self.starting_nodes[i] = newNode
                except Exception:
                    pass
        self.RemoveNode(*oldNode)
        self.UpdateAdjacencyMatrix()

    def ReplicateConnections(self, newNode: Node, *oldNodes: Node):
        """
        Replicate the connections of old nodes in the graph to the new node.
        - newNode: The node that will take over connections from old nodes.
        - oldNodes: One or more old nodes whose connections are transferred to the new node.
        """
        for oldNode in oldNodes:
            # Replicate predecessors (incoming connections)
            for pred in list(oldNode.predecessors):
                # add predecessor to newNode
                try:
                    if pred in self.nodes:
                        newNode.AddPreNode(pred)
                except Exception:
                    pass
            # Replicate outgoing connections (connections from the old node to others)
            if oldNode in self.nodes:
                oldNodeIndex = self.nodes.index(oldNode)
                for j in range(len(self.adjacencyMatrix[oldNodeIndex])):
                    if (
                        self.adjacencyMatrix[oldNodeIndex][j] == 1
                    ):  # If old node connects to another node
                        self.nodes[j].AddPreNode(newNode)

        # Recompute adjacency matrix to reflect new connections
        self.UpdateAdjacencyMatrix()

    def TransferNodeAttributes(self, oldNode: Node, newNode: Node):
        """Copy transferable attributes from oldNode to newNode.

        This attempts to copy primitive and simple attributes (like value, data, buffer, size).
        We avoid copying complex object references (predecessors, id) as those are handled separately.
        """
        if oldNode is None or newNode is None:
            return
        # Copy simple attributes if they exist on both nodes
        simple_attrs = [
            "value",
            "data",
            "size",
            "index",
            "inputCount",
            "batchSize",
            "inclusive",
            "forcedBatchProcessing",
        ]
        for attr in simple_attrs:
            try:
                if hasattr(oldNode, attr) and hasattr(newNode, attr):
                    setattr(newNode, attr, getattr(oldNode, attr))
            except Exception:
                pass
        # Special-case ContainerNode initial value
        try:
            if (
                getattr(oldNode, "__class__", None) is not None
                and getattr(newNode, "__class__", None) is not None
            ):
                if (
                    oldNode.__class__.__name__ == "ContainerNode"
                    and hasattr(oldNode, "value")
                    and hasattr(newNode, "value")
                ):
                    newNode.value = oldNode.value
        except Exception:
            pass

    def CompressNodes(self, nodes):
        """
        Create a CompressedNode from a set of nodes.
        """
        compressed = CompressedNode("", nodes)
        self.RemoveNode(*nodes)
        self.AddNode(compressed)
        return compressed

    def DisplayGraph(self, fileName="ComputationalGraph"):
        """Visualize the MLP graph in a left-to-right layout using Graphviz."""
        dot = Digraph(format="svg")
        dot.attr(rankdir="LR")  # Set the layout to be left-to-right
        for node in self.nodes:
            dot.node(
                node.name, label=f"{node.name}\n({type(node).__name__})\n{node.value}"
            )
        for i, row in enumerate(self.adjacencyMatrix):
            for j, connection in enumerate(row):
                if connection == 1:
                    dot.edge(self.nodes[i].name, self.nodes[j].name)
        dot.render(filename=fileName, view=True)

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

    def BuildSuccessorMap(self):
        """
        Build a dictionary mapping each node to its list of successor nodes.
        A successor is any node that has this node as a predecessor.

        Returns:
            dict: {node: [list of successor nodes]}
        """
        successor_map = {node: [] for node in self.nodes}

        for node in self.nodes:
            for predecessor in node.predecessors:
                if predecessor in successor_map:
                    successor_map[predecessor].append(node)

        return successor_map

    def analyze_topology(self):
        """
        Analyze the topology of the graph and classify each node into one of 9 types
        based on predecessor and successor counts.

        Topology types:
        - isolated: no predecessors, no successors (0, 0)
        - endpoint: 1 predecessor, no successors (1, 0)
        - entrypoint: no predecessors, 1 successor (0, 1)
        - link: 1 predecessor, 1 successor (1, 1)
        - greedy: >1 predecessors, no successors (>1, 0)
        - genesis: no predecessors, >1 successors (0, >1)
        - distribution: 1 predecessor, >1 successors (1, >1)
        - union: >1 predecessors, 1 successor (>1, 1)
        - cross: >1 predecessors, >1 successors (>1, >1)

        Returns:
            dict: {node: topology_type_string} mapping each node to its type
        """
        successor_map = self.BuildSuccessorMap()
        topology_map = {}

        for node in self.nodes:
            pred_count = len(node.predecessors)
            succ_count = len(successor_map.get(node, []))

            # Classify based on predecessor/successor counts
            if pred_count == 0 and succ_count == 0:
                topo_type = "isolated"
            elif pred_count == 1 and succ_count == 0:
                topo_type = "endpoint"
            elif pred_count == 0 and succ_count == 1:
                topo_type = "entrypoint"
            elif pred_count == 1 and succ_count == 1:
                topo_type = "link"
            elif pred_count > 1 and succ_count == 0:
                topo_type = "greedy"
            elif pred_count == 0 and succ_count > 1:
                topo_type = "genesis"
            elif pred_count == 1 and succ_count > 1:
                topo_type = "distribution"
            elif pred_count > 1 and succ_count == 1:
                topo_type = "union"
            else:  # pred_count > 1 and succ_count > 1
                topo_type = "cross"

            node.topology_type = topo_type
            topology_map[node] = topo_type

        return topology_map

    def set_manual_processing_sequence(self, sequence, strict=True):
        """
        Set a manual processing sequence for the graph. The sequence should be a list of
        iterables (sets, lists, tuples) each containing node identifiers (Node instance, id string, or index).
        If strict is True, invalid identifiers raise ValueError; otherwise they are ignored.
        """
        if sequence is None:
            self.manual_processing_sequence = None
            return

        resolved_sequence = []
        for step in sequence:
            if step is None:
                continue
            step_list = []
            for entry in step:
                # Accept Node objects, id strings, or indices
                if isinstance(entry, Node):
                    node_obj = entry
                elif isinstance(entry, str):
                    node_obj = self.idToNodeDictionary.get(entry)
                    if node_obj is None:
                        # Try matching by name
                        matches = [
                            n for n in self.nodes if getattr(n, "name", None) == entry
                        ]
                        if len(matches) == 1:
                            node_obj = matches[0]
                        elif len(matches) > 1:
                            if strict:
                                raise ValueError(
                                    f"Ambiguous node name '{entry}' matches multiple nodes."
                                )
                            else:
                                node_obj = matches[0]
                elif isinstance(entry, int):
                    try:
                        node_obj = self.nodes[entry]
                    except IndexError:
                        node_obj = None
                else:
                    node_obj = None

                if node_obj is None:
                    if strict:
                        raise ValueError(
                            f"Node identifier '{entry}' not found in graph."
                        )
                    else:
                        continue

                if node_obj not in self.nodes:
                    if strict:
                        raise ValueError(
                            f"Node '{node_obj}' is not part of this graph."
                        )
                    else:
                        continue

                if node_obj not in step_list:
                    step_list.append(node_obj)

            # Only add non-empty steps
            if step_list:
                resolved_sequence.append(step_list)

        self.manual_processing_sequence = resolved_sequence

    def clear_manual_processing_sequence(self):
        """Clear any previously set manual processing sequence."""
        self.manual_processing_sequence = None

    # any node that old nodes are in its pred list
    # put the new abstract node in its pred list

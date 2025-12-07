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
        Create a CompressedNode from a chain of sequentially connected nodes.

        The nodes must form a valid compressible chain (use can_compress_nodes()
        to validate first). The compressed node will:
        - Have predecessors = first node's external predecessors
        - Have successors = last node's external successors
        - Process contained nodes sequentially when computed

        Args:
            nodes: List of nodes to compress (will be ordered into chain)

        Returns:
            The created CompressedNode, or None if compression failed
        """
        if not nodes or len(nodes) < 2:
            return None

        # Update topology types before compression validation
        self.analyze_topology()

        # Order nodes into chain sequence
        ordered = self._order_nodes_into_chain(nodes)
        if ordered is None:
            return None

        first_node = ordered[0]
        last_node = ordered[-1]

        # Get external predecessors (predecessors of first node not in chain)
        nodes_set = set(ordered)
        external_preds = [p for p in first_node.predecessors if p not in nodes_set]

        # Get external successors (successors of last node not in chain)
        successor_map = self.BuildSuccessorMap()
        external_succs = [
            s for s in successor_map.get(last_node, []) if s not in nodes_set
        ]

        # Create the compressed node with ordered internal nodes
        compressed = CompressedNode("", ordered)

        # Add the compressed node to the graph (gets C1, C2, etc. ID)
        self.AddNode(compressed)

        # Set the name to match the ID (C1, C2, etc.)
        compressed.name = compressed.id

        # Copy the last node's value to the compressed node
        compressed.value = last_node.value

        # Set up external connections:
        # 1. External predecessors -> CompressedNode
        for pred in external_preds:
            compressed.AddPreNode(pred)

        # 2. CompressedNode -> External successors
        for succ in external_succs:
            # Replace the last_node in succ's predecessors with compressed node
            if last_node in succ.predecessors:
                succ.predecessors.remove(last_node)
            succ.AddPreNode(compressed)

        # Handle starting_nodes: if any compressed node was a starting node,
        # replace with the compressed node
        for i, sn in enumerate(list(self.starting_nodes)):
            if sn in nodes_set:
                self.starting_nodes[i] = compressed
        # Remove duplicates from starting_nodes
        seen = set()
        new_starting = []
        for sn in self.starting_nodes:
            if sn not in seen:
                seen.add(sn)
                new_starting.append(sn)
        self.starting_nodes = new_starting

        # Remove the original nodes from the graph
        # (but they remain in the CompressedNode's listOfNodes)
        for node in ordered:
            if node in self.nodes:
                index = self.nodes.index(node)
                # Remove from adjacency matrix
                self.__RemoveNodeFromAdjacencyMatrix(index)
                # Remove from nodes list and dictionary
                self.nodes.remove(node)
                if node.id in self.idToNodeDictionary:
                    del self.idToNodeDictionary[node.id]

        # Rebuild adjacency matrix to reflect new structure
        self.UpdateAdjacencyMatrix()

        return compressed

    def _order_nodes_into_chain(self, nodes):
        """
        Order a set of nodes into a sequential chain based on connections.

        Args:
            nodes: Iterable of nodes to order

        Returns:
            Ordered list from first (entry) to last (exit), or None if invalid
        """
        nodes_set = set(nodes)
        if len(nodes_set) < 2:
            return list(nodes_set) if nodes_set else None

        successor_map = self.BuildSuccessorMap()

        # Find the entry point: node whose predecessors are all external
        entry_node = None
        for node in nodes_set:
            internal_preds = [p for p in node.predecessors if p in nodes_set]
            if len(internal_preds) == 0:
                if entry_node is not None:
                    # Multiple entry points - not a simple chain
                    return None
                entry_node = node

        if entry_node is None:
            # No entry point found (cycle within selection?)
            return None

        # Build chain by following successors
        ordered = [entry_node]
        current = entry_node
        visited = {entry_node}

        while len(ordered) < len(nodes_set):
            # Find next node in chain (successor that's in our set)
            succs_in_set = [
                s
                for s in successor_map.get(current, [])
                if s in nodes_set and s not in visited
            ]
            if len(succs_in_set) != 1:
                # No successor or multiple successors in selection
                return None
            next_node = succs_in_set[0]
            ordered.append(next_node)
            visited.add(next_node)
            current = next_node

        return ordered

    def can_compress_nodes(self, nodes):
        """
        Check if a set of nodes can be compressed into a CompressedNode.

        Valid compression requires:
        1. At least 2 nodes
        2. Nodes form a single connected chain (no branching within)
        3. First node: entrypoint, link, or union topology
        4. Last node: endpoint, link, or distribution topology
        5. Middle nodes: link topology only (1 pred, 1 succ)
        6. No external predecessors on internal (middle) nodes

        Args:
            nodes: Iterable of nodes to check

        Returns:
            tuple: (can_compress: bool, reason: str)
        """
        nodes_list = list(nodes)
        if len(nodes_list) < 2:
            return (False, "Need at least 2 nodes to compress")

        # Ensure topology is analyzed
        self.analyze_topology()

        # Try to order into chain
        ordered = self._order_nodes_into_chain(nodes_list)
        if ordered is None:
            return (False, "Nodes don't form a connected chain")

        nodes_set = set(ordered)
        successor_map = self.BuildSuccessorMap()

        first_node = ordered[0]
        last_node = ordered[-1]
        middle_nodes = ordered[1:-1] if len(ordered) > 2 else []

        # Check first node topology
        valid_first = {"entrypoint", "link", "union"}
        first_topo = getattr(first_node, "topology_type", None)
        if first_topo not in valid_first:
            return (
                False,
                f"First node '{first_node.name}' has invalid "
                f"topology '{first_topo}' (need {valid_first})",
            )

        # Check last node topology
        valid_last = {"endpoint", "link", "distribution"}
        last_topo = getattr(last_node, "topology_type", None)
        if last_topo not in valid_last:
            return (
                False,
                f"Last node '{last_node.name}' has invalid "
                f"topology '{last_topo}' (need {valid_last})",
            )

        # Check middle nodes: must be link type and no external predecessors
        for node in middle_nodes:
            node_topo = getattr(node, "topology_type", None)
            if node_topo != "link":
                return (
                    False,
                    f"Middle node '{node.name}' must be 'link' "
                    f"topology, got '{node_topo}'",
                )

            # Check for external predecessors
            external_preds = [p for p in node.predecessors if p not in nodes_set]
            if external_preds:
                ext_names = [p.name for p in external_preds]
                return (
                    False,
                    f"Middle node '{node.name}' has external "
                    f"predecessors: {ext_names}",
                )

        return (True, "Nodes can be compressed")

    def DecompressNode(self, compressed_node, mode="full"):
        """
        Decompress a CompressedNode, restoring its internal nodes to the graph.

        Modes:
        - 'full': Restore all internal nodes, remove the CompressedNode
        - 'pop_first': Extract only the first node, keep rest compressed
        - 'pop_last': Extract only the last node, keep rest compressed

        Args:
            compressed_node: The CompressedNode to decompress
            mode: One of 'full', 'pop_first', 'pop_last'

        Returns:
            List of restored nodes, or None if failed
        """
        if not isinstance(compressed_node, CompressedNode):
            return None
        if compressed_node not in self.nodes:
            return None
        if not compressed_node.listOfNodes:
            return None

        successor_map = self.BuildSuccessorMap()
        external_preds = list(compressed_node.predecessors)
        external_succs = successor_map.get(compressed_node, [])

        if mode == "full":
            return self._decompress_full(
                compressed_node, external_preds, external_succs
            )
        elif mode == "pop_first":
            return self._decompress_pop_first(compressed_node, external_preds)
        elif mode == "pop_last":
            return self._decompress_pop_last(compressed_node, external_succs)
        else:
            return None

    def _decompress_full(self, compressed_node, external_preds, external_succs):
        """Fully decompress: restore all internal nodes."""
        internal_nodes = compressed_node.get_internal_nodes()
        first_node = internal_nodes[0]
        last_node = internal_nodes[-1]

        # Add all internal nodes back to graph
        for node in internal_nodes:
            self.AddNode(node)

        # Reconnect external predecessors to first node
        for pred in external_preds:
            first_node.AddPreNode(pred)

        # Reconnect external successors from last node
        for succ in external_succs:
            if compressed_node in succ.predecessors:
                succ.predecessors.remove(compressed_node)
            succ.AddPreNode(last_node)

        # Handle starting_nodes
        if compressed_node in self.starting_nodes:
            idx = self.starting_nodes.index(compressed_node)
            self.starting_nodes[idx] = first_node

        # Remove the compressed node from graph manually
        # (can't use RemoveNode because successors already updated)
        if compressed_node in self.nodes:
            index = self.nodes.index(compressed_node)
            # Remove from adjacency matrix
            self.__RemoveNodeFromAdjacencyMatrix(index)
            # Remove from nodes list and dictionary
            self.nodes.remove(compressed_node)
            if compressed_node.id in self.idToNodeDictionary:
                del self.idToNodeDictionary[compressed_node.id]

        self.UpdateAdjacencyMatrix()

        return internal_nodes

    def _decompress_pop_first(self, compressed_node, external_preds):
        """Extract the first node, keep rest compressed."""
        if len(compressed_node.listOfNodes) <= 1:
            # Only one node left, do full decompress
            return self._decompress_full(
                compressed_node,
                external_preds,
                self.BuildSuccessorMap().get(compressed_node, []),
            )

        first_node = compressed_node.pop_front()
        new_first = compressed_node.first_node

        # Add extracted node to graph
        self.AddNode(first_node)

        # External predecessors now connect to extracted node
        for pred in external_preds:
            first_node.AddPreNode(pred)
            # Remove from compressed node's predecessors
            if pred in compressed_node.predecessors:
                compressed_node.predecessors.remove(pred)

        # Extracted node connects to compressed node
        compressed_node.AddPreNode(first_node)

        # Handle starting_nodes
        if compressed_node in self.starting_nodes:
            idx = self.starting_nodes.index(compressed_node)
            self.starting_nodes.insert(idx, first_node)

        self.UpdateAdjacencyMatrix()
        return [first_node]

    def _decompress_pop_last(self, compressed_node, external_succs):
        """Extract the last node, keep rest compressed."""
        if len(compressed_node.listOfNodes) <= 1:
            return self._decompress_full(
                compressed_node, list(compressed_node.predecessors), external_succs
            )

        last_node = compressed_node.pop_back()

        # Add extracted node to graph
        self.AddNode(last_node)

        # Extracted node's predecessor is the compressed node
        last_node.AddPreNode(compressed_node)

        # External successors now connect from extracted node
        for succ in external_succs:
            if compressed_node in succ.predecessors:
                succ.predecessors.remove(compressed_node)
            succ.AddPreNode(last_node)

        self.UpdateAdjacencyMatrix()
        return [last_node]

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

    # =========================================================================
    # Abstraction methods - grouping disjoint nodes with same predecessors/successors
    # =========================================================================

    def can_abstract_nodes(self, nodes):
        """
        Check if a set of nodes can be abstracted into an AbstractNode.

        Valid abstraction requires:
        1. At least 2 nodes
        2. Nodes are disjoint (no edges between them)
        3. All nodes share the same predecessors
        4. All nodes share the same successors

        Args:
            nodes: Iterable of nodes to check

        Returns:
            tuple: (can_abstract: bool, reason: str)
        """
        nodes_list = list(nodes)
        if len(nodes_list) < 2:
            return (False, "Need at least 2 nodes to abstract")

        nodes_set = set(nodes_list)

        # Build successor map for successor checking
        successor_map = self.BuildSuccessorMap()

        # Check that nodes are disjoint (no edges between them)
        for node in nodes_list:
            # Check predecessors - none should be in the selection
            for pred in node.predecessors:
                if pred in nodes_set:
                    return (
                        False,
                        f"Node '{node.name}' has predecessor '{pred.name}' "
                        f"in selection - nodes must be disjoint",
                    )
            # Check successors - none should be in the selection
            for succ in successor_map.get(node, []):
                if succ in nodes_set:
                    return (
                        False,
                        f"Node '{node.name}' has successor '{succ.name}' "
                        f"in selection - nodes must be disjoint",
                    )

        # Get reference predecessors and successors from first node
        reference_node = nodes_list[0]
        reference_preds = set(reference_node.predecessors)
        reference_succs = set(successor_map.get(reference_node, []))

        # Check all other nodes have the same predecessors and successors
        for node in nodes_list[1:]:
            node_preds = set(node.predecessors)
            node_succs = set(successor_map.get(node, []))

            if node_preds != reference_preds:
                diff_preds = node_preds.symmetric_difference(reference_preds)
                diff_names = [p.name for p in diff_preds]
                return (
                    False,
                    f"Node '{node.name}' has different predecessors than "
                    f"'{reference_node.name}': {diff_names}",
                )

            if node_succs != reference_succs:
                diff_succs = node_succs.symmetric_difference(reference_succs)
                diff_names = [s.name for s in diff_succs]
                return (
                    False,
                    f"Node '{node.name}' has different successors than "
                    f"'{reference_node.name}': {diff_names}",
                )

        return (True, "Nodes can be abstracted")

    def AbstractNodes(self, nodes):
        """
        Create an AbstractNode from a set of disjoint nodes with same predecessors/successors.

        The nodes must be valid for abstraction (use can_abstract_nodes() to validate first).
        The abstract node will:
        - Have predecessors = shared predecessors of all internal nodes
        - Have successors = shared successors of all internal nodes
        - Process contained nodes in parallel when computed

        Args:
            nodes: List of disjoint nodes to abstract

        Returns:
            The created AbstractNode, or None if abstraction failed
        """
        if not nodes or len(nodes) < 2:
            return None

        nodes_list = list(nodes)
        nodes_set = set(nodes_list)

        # Validate abstraction is possible
        can_abstract, reason = self.can_abstract_nodes(nodes_list)
        if not can_abstract:
            return None

        successor_map = self.BuildSuccessorMap()

        # Get shared predecessors and successors (from any node, they're all the same)
        shared_preds = list(nodes_list[0].predecessors)
        shared_succs = list(successor_map.get(nodes_list[0], []))

        # Create the abstract node with internal nodes
        abstract = AbstractNode("", nodes_list)

        # Add the abstract node to the graph (gets A1, A2, etc. ID)
        self.AddNode(abstract)

        # Set the name to match the ID (A1, A2, etc.)
        abstract.name = abstract.id

        # Set up external connections:
        # 1. Shared predecessors -> AbstractNode
        for pred in shared_preds:
            abstract.AddPreNode(pred)

        # 2. AbstractNode -> Shared successors
        # Replace all internal nodes in successors' predecessors with abstract node
        for succ in shared_succs:
            # Remove all internal nodes from successor's predecessors
            for node in nodes_list:
                if node in succ.predecessors:
                    succ.predecessors.remove(node)
            # Add abstract node as predecessor
            succ.AddPreNode(abstract)

        # Handle starting_nodes: if any abstracted node was a starting node,
        # replace with the abstract node
        for i, sn in enumerate(list(self.starting_nodes)):
            if sn in nodes_set:
                self.starting_nodes[i] = abstract
        # Remove duplicates from starting_nodes
        seen = set()
        new_starting = []
        for sn in self.starting_nodes:
            if sn not in seen:
                seen.add(sn)
                new_starting.append(sn)
        self.starting_nodes = new_starting

        # Remove the original nodes from the graph
        # (but they remain in the AbstractNode's listOfNodes)
        for node in nodes_list:
            if node in self.nodes:
                index = self.nodes.index(node)
                # Remove from adjacency matrix
                self.__RemoveNodeFromAdjacencyMatrix(index)
                # Remove from nodes list and dictionary
                self.nodes.remove(node)
                if node.id in self.idToNodeDictionary:
                    del self.idToNodeDictionary[node.id]

        # Rebuild adjacency matrix to reflect new structure
        self.UpdateAdjacencyMatrix()

        return abstract

    def ExpandAbstractNode(self, abstract_node):
        """
        Expand an AbstractNode, restoring its internal nodes to the graph.

        The internal nodes are restored with their shared predecessors and successors.

        Args:
            abstract_node: The AbstractNode to expand

        Returns:
            List of restored nodes, or None if failed
        """
        if not isinstance(abstract_node, AbstractNode):
            return None
        if abstract_node not in self.nodes:
            return None
        if not abstract_node.listOfNodes:
            return None

        internal_nodes = abstract_node.get_internal_nodes()
        successor_map = self.BuildSuccessorMap()
        external_preds = list(abstract_node.predecessors)
        external_succs = successor_map.get(abstract_node, [])

        # Add all internal nodes back to graph
        for node in internal_nodes:
            self.AddNode(node)

        # Reconnect external predecessors to all internal nodes
        for node in internal_nodes:
            for pred in external_preds:
                node.AddPreNode(pred)

        # Reconnect external successors from all internal nodes
        for succ in external_succs:
            if abstract_node in succ.predecessors:
                succ.predecessors.remove(abstract_node)
            for node in internal_nodes:
                succ.AddPreNode(node)

        # Handle starting_nodes: if abstract was a starting node, replace with
        # first internal node (arbitrary choice, all have same predecessors)
        if abstract_node in self.starting_nodes:
            idx = self.starting_nodes.index(abstract_node)
            self.starting_nodes[idx] = internal_nodes[0]

        # Remove the abstract node from graph manually
        if abstract_node in self.nodes:
            index = self.nodes.index(abstract_node)
            self.__RemoveNodeFromAdjacencyMatrix(index)
            self.nodes.remove(abstract_node)
            if abstract_node.id in self.idToNodeDictionary:
                del self.idToNodeDictionary[abstract_node.id]

        self.UpdateAdjacencyMatrix()

        return internal_nodes

    # any node that old nodes are in its pred list
    # put the new abstract node in its pred list

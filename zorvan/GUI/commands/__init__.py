"""
Undo/Redo command classes for the ComputationalGraphs GUI.

This module provides QUndoCommand subclasses for all undoable UI operations:
- AddNodeCommand: Adding a node to the canvas
- RemoveItemsCommand: Removing nodes and edges
- MoveNodesCommand: Moving nodes
- AddEdgeCommand: Adding an edge between nodes
- RemoveEdgeCommand: Removing an edge
- PasteCommand: Pasting nodes and edges from clipboard
- SwallowNodeCommand: Removing nodes while reconnecting predecessors to successors
- ReplaceNodeCommand: Replacing a node with a different type
- CompressNodeCommand: Compressing sequential nodes into a CompressedNode
- DecompressNodeCommand: Decompressing a CompressedNode back to original nodes
- AbstractNodeCommand: Abstracting disjoint nodes into an AbstractNode
- ExpandAbstractNodeCommand: Expanding an AbstractNode back to original nodes
- SimplifyStepCommand: Apply one simplification step
- FullySimplifyCommand: Apply all possible simplifications
- ExpandStepCommand: Reverse the last simplification
"""

from .abstract_node_command import AbstractNodeCommand, ExpandAbstractNodeCommand
from .add_edge_command import AddEdgeCommand
from .add_node_command import AddNodeCommand
from .compress_node_command import CompressNodeCommand, DecompressNodeCommand
from .move_nodes_command import MoveNodesCommand
from .paste_command import PasteCommand
from .remove_edge_command import RemoveEdgeCommand
from .remove_items_command import RemoveItemsCommand
from .replace_node_command import ReplaceNodeCommand
from .simplify_command import (
    ExpandStepCommand,
    FullySimplifyCommand,
    SimplifyStepCommand,
)
from .swallow_node_command import SwallowNodeCommand

__all__ = [
    "AddNodeCommand",
    "RemoveItemsCommand",
    "MoveNodesCommand",
    "AddEdgeCommand",
    "RemoveEdgeCommand",
    "PasteCommand",
    "ReplaceNodeCommand",
    "SwallowNodeCommand",
    "CompressNodeCommand",
    "DecompressNodeCommand",
    "AbstractNodeCommand",
    "ExpandAbstractNodeCommand",
    "SimplifyStepCommand",
    "FullySimplifyCommand",
    "ExpandStepCommand",
]

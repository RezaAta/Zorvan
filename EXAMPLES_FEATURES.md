# Examples and Automation Features - Implementation Summary

## Overview
Successfully added Examples menu and MLP/Backpropagation automation tools to your ComputationalGraphs GUI.

## New Files Created

### 1. `examples_loader.py`
- **Purpose**: Manages example graph templates
- **Features**:
  - Organized categories: Basic, Neural Networks, Fuzzy Systems, Evolutionary Algorithms
  - 7 example graphs ready to load
  - Easy to extend with more examples

**Available Examples:**
- **Basic**:
  - Fibonacci Sequence (recursive computation)
  - Simple Addition Chain (sequential operations)
  
- **Neural Networks**:
  - XOR Problem (2-2-1 with backpropagation)
  - Simple MLP (1-1-1 minimal network)
  - Iris Classification (4-5-3-3 multi-class)
  
- **Fuzzy Systems**:
  - Temperature Control (fan speed control)
  
- **Evolutionary Algorithms**:
  - De Jong Sphere Function (genetic optimization)

### 2. `mlp_dialog.py`
- **Purpose**: Interactive MLP generator
- **Features**:
  - Configure inputs, outputs, hidden layers
  - Choose activation functions (Sigmoid, ReLU, Linear)
  - Dynamic layer size controls
  - Real-time validation
  
**Usage**: Tools → Generate MLP... (Ctrl+M)

### 3. `backprop_dialog.py`
- **Purpose**: Add backpropagation to existing MLPs
- **Features**:
  - Configurable learning rate
  - Validates MLP structure
  - Combines forward and backward passes
  
**Usage**: Tools → Add Backpropagation... (Ctrl+B)

## Modified Files

### `main_window.py`
**New Menu Structure:**
```
File
├── New
├── Open...
├── Save
├── ──────────
├── Examples >
│   ├── Basic >
│   │   ├── Fibonacci Sequence
│   │   └── Simple Addition Chain
│   ├── Neural Networks >
│   │   ├── XOR Problem (2-2-1)
│   │   ├── Simple MLP (1-1-1)
│   │   └── Iris Classification (4-5-3-3)
│   ├── Fuzzy Systems >
│   │   └── Temperature Control (Fan Speed)
│   └── Evolutionary Algorithms >
│       └── De Jong Sphere Function
├── ──────────
└── Exit

Tools (NEW!)
├── Generate MLP... (Ctrl+M)
└── Add Backpropagation... (Ctrl+B)
```

**New Methods:**
- `_populate_examples_menu()`: Builds dynamic examples menu
- `_load_example()`: Loads and visualizes example graphs
- `_show_mlp_dialog()`: Opens MLP generator
- `_show_backprop_dialog()`: Opens backprop dialog
- `_visualize_graph_on_canvas()`: Converts Graph objects to visual nodes/edges

### `__init__.py`
Updated to export new modules for cleaner imports.

## How to Use

### Loading Examples
1. Click **File → Examples**
2. Navigate to category (e.g., Neural Networks)
3. Click example name
4. Graph loads automatically with visual layout
5. Click **▶ Start** to run the example

### Generating Custom MLPs
1. Click **Tools → Generate MLP...** (or Ctrl+M)
2. Configure architecture:
   - Number of inputs (e.g., 4 for Iris)
   - Number of outputs (e.g., 3 for 3 classes)
   - Hidden layers (e.g., 2 layers)
   - Layer sizes (e.g., 5 and 3 neurons)
3. Choose activation functions
4. Click **Generate**
5. MLP appears on canvas with automatic layout

### Adding Backpropagation
1. Load or generate an MLP
2. Click **Tools → Add Backpropagation...** (or Ctrl+B)
3. Set learning rate (default: 0.01)
4. Click **Add Backpropagation**
5. Backward pass nodes are added to graph
6. Ready for training

## Technical Details

### Graph Visualization Algorithm
The `_visualize_graph_on_canvas()` method:
1. Creates NetworkX DiGraph from your Graph object
2. Uses spring layout algorithm for node positioning
3. Scales coordinates to canvas size
4. Creates NodeItem for each node
5. Creates EdgeItem for each connection
6. Applies current color scheme

### Example Builder Pattern
Each example uses a builder function:
```python
def _build_fibonacci(self) -> Graph:
    graph = Graph()
    # ... construct nodes and connections
    graph.UpdateAdjacencyMatrix()
    return graph
```

This pattern:
- ✅ Generates fresh graphs each time
- ✅ Can include random initialization
- ✅ Self-contained and testable
- ✅ Easy to add new examples

### Error Handling
All dialogs include:
- Input validation
- Exception catching with user-friendly messages
- Graceful fallbacks
- Status bar updates

## Adding New Examples

To add your own example:

1. Open `examples_loader.py`
2. Add builder method:
```python
def _build_my_example(self) -> Graph:
    graph = Graph()
    # Your graph construction here
    graph.UpdateAdjacencyMatrix()
    return graph
```

3. Register in `_register_examples()`:
```python
category.add_example(
    "My Example Name",
    "Description shown in status bar",
    self._build_my_example
)
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+M | Generate MLP |
| Ctrl+B | Add Backpropagation |
| Ctrl+N | New Graph |
| Ctrl+O | Open File |
| Ctrl+S | Save File |
| Ctrl+E | Edit Selected Node |
| Delete | Remove Selected |
| F5 | Run Graph |

## Dependencies

Installed via `requirements_gui.txt`:
- **PyQt6 >= 6.4.0**: GUI framework
- **networkx >= 2.8.0**: Graph layout algorithms

## Testing Checklist

- [x] Examples menu appears in File menu
- [x] All 7 examples load without errors
- [x] MLP dialog opens and generates networks
- [x] Backprop dialog validates and adds training
- [x] Generated graphs visualize on canvas
- [x] Graphs can be executed with Start button
- [x] Status bar shows helpful messages
- [x] Keyboard shortcuts work

## Known Limitations

1. **Large Graphs**: Visualization may be slow for >100 nodes
2. **Layout Quality**: Spring layout isn't perfect for all topologies
   - Solution: Use Layout buttons (Spring/Hierarchical/Circular)
3. **MLP Validation**: Backprop dialog accepts any graph
   - Warning shown if not MLPGraph instance

## Future Enhancements

Potential improvements:
- [ ] Save examples as .drawio files
- [ ] Import examples from user folder
- [ ] More layout algorithms (tree, radial)
- [ ] Example preview thumbnails
- [ ] Parameter customization for examples
- [ ] Export example as Python code
- [ ] Training data loading for MLPs
- [ ] Real-time loss plotting

## Troubleshooting

**Example won't load:**
- Check Console for Python errors
- Verify all node types exist in Nodes/ folder
- Check if Graph.UpdateAdjacencyMatrix() succeeds

**MLP generation fails:**
- Ensure hidden layer count matches sizes list
- Verify activation function nodes exist
- Check console for detailed error

**Visualization looks wrong:**
- Try different layout algorithms
- Manually drag nodes to adjust
- Check if edges connect to correct nodes

## Architecture Notes

The implementation maintains separation of concerns:
- **examples_loader.py**: Pure Graph construction (no GUI)
- **mlp_dialog.py**: UI only, delegates to MLPGraph
- **backprop_dialog.py**: UI only, delegates to BackpropGraph
- **main_window.py**: Orchestrates UI and Graph objects

This design allows:
- Unit testing of graph builders
- Reusing examples in non-GUI contexts
- Easy extension without modifying core classes

## Success!

Your GUI now has:
✅ 7 ready-to-use example graphs
✅ Interactive MLP generator
✅ One-click backpropagation
✅ Professional menu structure
✅ Automatic graph visualization
✅ Keyboard shortcuts for power users

The examples showcase your framework's capabilities and make it easy for users to get started!

## Manual Processing Mode (New)

Manual Processing is a lightweight execution mode where the user provides a sequence of node groups to execute. Each step in the sequence is one iteration and consists of a set/list of nodes to process. The processor executes UpdateInputs() and ProcessBatch() for each node in the set in the order you provide.

Key points:
- Stored on the Graph as `graph.manual_processing_sequence` (use `graph.set_manual_processing_sequence(sequence)` to set it).
- Run via `processor.ManualProcessing(iterations, computation_sequence=sequence)`.
- This mode does not perform dependency checks or graph initialization — you are responsible for providing a valid sequence.
- If no sequence is provided, `ManualProcessing` falls back to `ForwardProcessing`.

Example:
```python
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode

graph = Graph()
a = DataStreamNode('a', data=[1,2,3])
b = DataStreamNode('b', data=[10,20,30])
c = AdditionNode('c')
c.AddPreNode(a, b)
graph.AddNode(a, b, c)

# The manual sequence: first update both streams, then compute the addition
sequence = [[a, b], [c]]
proc = GraphProcessor(graph)
proc.ManualProcessing(iterations=3, computation_sequence=sequence)
```


# Copilot Instructions (Concise)

These concise rules help AI coding agents make productive, correct edits in this repo.

- Quick Commands:
  - Create virtualenv & bootstrap (Windows PowerShell):
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    .\scripts\bootstrap.ps1
    ```
  - Run GUI: `python run_gui.py`
  - Quick tests: `python ClassicMLPTestOnXOR.py`, `python CompareThreeApproaches.py`
  - Full test suite: `pytest -q`

- Big picture: Node-centric computational graphs. Nodes are active actors; Graphs orchestrate nodes.
- Processing modes: `concurrent` (buffers) vs `forward` (active node propagation). They are distinct — don’t mix models without a design change.
- Key files: `ComputationalGraphs/Core/Graph.py`, `GraphProcessor.py`, `MLPGraph.py`, `MLPGraphForwardProcessing.py`, `BackpropGraph.py`, `BackpropGraphForwardProcessing.py`.
- Important nodes: `ContainerNode` (weights), `BufferNode` (timing), `DataStreamNode` (inputs), `MultiplicationNode`, activations.
- Conventions & gotchas:
  - Weight node naming: `W_x{input}H{layer}N{neuron}` and `W_H{layer}N{node}y{output}`.
  - Data shapes differ: `MLPGraph`=features x samples; forward MLP=samples x features.
  - Buffer size formula: `(layersAhead * 6)`—don’t change lightly.
  - Call `graph.UpdateAdjacencyMatrix()` after modifying connections.
  - Forward-processing: call `mlp.PrepareForForwardProcessing(processor)` to mark sources & `ContainerNode`s processed.

- When editing:
  - Prefer small, focused edits. Use `apply_patch` for file edits; add tests for behavioral changes.
  - For backprop/MLP edits add tests (e.g., XOR) and run quick sanity checks.
  - Avoid moving node-local logic into a central controller—nodes are actors.

- Integration & testing:
  - GUI: `run_gui.py` and `ComputationalGraphs/GUI/` for visual debugging.
  - Examples: `Examples/` and the `Compare*` scripts provide representative workflows.
  - Run `pytest -q`; GUI tests require `requirements_gui.txt` and Xvfb on CI for headless runs.

- Contribution notes: follow `AGENT_POLICY.md` and `DEVELOPER_GUIDE.md` (TDD, small commits, `git cz`, pre-commit hooks).

If a change touches the core execution model or timing (concurrent vs forward), open an issue and get design approval before implementing.


### 1. Concurrent Processing (`ComputeGraph`)
**Inspiration**: Complex systems and emergent behavior in parallel networks

- **How**: All nodes compute in each timestep/iteration simultaneously
- **Philosophy**: Simulation-based approach where emergent intelligence arises from parallel interactions
- **Challenge**: Neural networks block data flow - batch n must complete, update weights, before batch n+1
- **Solution**: BufferNodes for synchronization (introduces gradient delay issue - see Known Issues)

### 2. Forward Processing (`ForwardProcessing`)
**Inspiration**: Non-deterministic automata with active node propagation

- **How**: Only "active nodes" (whose predecessors completed) compute per iteration (1 computation per active node)
- **Philosophy**: Sequential propagation where each iteration processes nodes whose predecessors have completed
- **Source node reactivation**: Source nodes (no predecessors) are automatically reactivated when needed by successors in cycles
- **Advantage**: No buffers needed, eliminates gradient delay problem
- **Status**: Current implementation focus for neural network training

**Critical:** MLPGraph/BackpropGraph use concurrent mode. MLPGraphForwardProcessing/BackpropGraphForwardProcessing use forward processing mode. These are **fundamentally different execution models** - see `ARCHITECTURE_COMPARISON.md`.

### Node Hierarchy

All computational nodes inherit from `Node` (abstract base):
- **BasicNode**: Simple operations (AdditionNode, MultiplicationNode, etc.)
- **AbstractNode**: Contains sub-graphs (processes internal nodes in parallel)
- **CompressedNode**: Special compressed representations

Node naming follows convention: `A1`, `A2` (Abstract), `C1`, `C2` (Compressed), `a`, `b`, `c` (Basic).

### Important Terminology

- **Starting nodes**: User-selected nodes active at iteration 0 (may or may not have predecessors). Set via `graph.starting_nodes`.
- **Source nodes**: Nodes with no predecessors (`len(node.predecessors) == 0`). Automatically reactivated in forward processing when needed by successors.

### Graph Structure

**Philosophy**: Graph is a container and orchestrator, not the computational unit.

- `Graph.nodes`: All nodes in execution order (the computational actors)
- `Graph.adjacencyMatrix`: Connection matrix for traversal (secondary to nodes, rebuilt via `UpdateAdjacencyMatrix()`)
- `Graph.starting_nodes`: Entry points (usually DataStreamNodes, weight ContainerNodes in forward processing)
- **Always call** `UpdateAdjacencyMatrix()` after modifying connections

**Key distinction**: Unlike traditional graph frameworks that compile to adjacency matrices, this framework keeps nodes as first-class objects that execute independently. The adjacency matrix is a navigation aid, not the execution target.

## Critical Design Patterns

### 1. BufferNode Synchronization (Concurrent Mode Only)

```python
# Input layer: DataStream + Buffer pairs
self.inputLayer = [(DataStreamNode(f"x{i}"),
                   BufferNode(f"Buff_x{i}", size=(layersAhead * 6)))
                   for i in range(numInputs)]
```

Buffer sizes calculated as `(layersAhead * 6)` - this timing is critical for synchronization. DO NOT change without understanding delay propagation.

**Why BufferNodes are Essential (Not the Problem)**:

BufferNodes solve a fundamental temporal coherence problem in concurrent processing:

- **The Problem**: When backprop for sample t₀ is triggered, the input/activation values have already moved forward by tₙ iterations (where tₙ = distance from input node to the backprop node that needs that value). Using the current values would make backprop terribly inaccurate.

- **The Solution**: BufferNodes store historical activation, input, and weight values so backpropagation can access the correct values from the relevant iteration. Similarly, weight buffers preserve the weight values used during the forward pass.

- **The Effect**: The only theoretical difference between concurrent MLP and classic SGD is that weight updates are delayed by the buffer depth. This may make convergence slightly "lazier" but should NOT cause value explosion.

- **Debugging Rule**: If values explode, the bug is in gradient computation or connection logic, NOT in the buffer mechanism itself. Check backprop connections, gradient flow, and learning rate handling before suspecting buffers.

### 2. Data Format Differences

**MLPGraph (concurrent)**: Expects **row-per-feature** format
```python
X = [[all_x0_values], [all_x1_values], ...]  # Shape: (features, samples)
```

**MLPGraphForwardProcessing (forward processing)**: Expects **row-per-sample** format, transposes internally
```python
X = [[x0, x1], [x0, x1], ...]  # Shape: (samples, features)
```

### 3. Starting Nodes Pattern

**Concurrent**: Only data source nodes
```python
self.starting_nodes = [input[0] for input in inputLayer] + labelLayer
```

**Forward Processing**: First operation nodes (NOT data sources!)
```python
# Starting nodes = nodes that perform the FIRST OPERATION
# For MLP: multiplication of inputs and weights in first hidden layer
self.starting_nodes = self.firstLayerMultNodes

# Before training, mark source nodes (inputs, weights, labels) as processed:
mlp.PrepareForForwardProcessing(processor)
```

**Critical**: Starting nodes perform operations. Source nodes (no predecessors) provide data and must be marked as 'processed' before training so starting nodes can access their values.

### 4. ContainerNode for Trainable Parameters

ContainerNodes accumulate gradient updates via predecessors:
```python
weightNode = ContainerNode(name=f"w{i}{j}", value=random.uniform(-1, 1))
dW = MultiplicationNode(name=f"dw{i}{j}")
dW.AddPreNode(input, gradient)
weightNode.AddPreNode(dW)  # Accumulates updates automatically
```

### 5. Node Atomicity and Output Convention

**Critical design principle**: Each node outputs exactly 1 instance of information.
- ✅ Preferred: Single scalar values (int, float, bool)
- ✅ Allowed: Arrays/lists (count as 1 instance, but discouraged)
- ❌ Anti-pattern: Multiple separate outputs from one node

**Why this matters**: Atomicity enables clean graph traversal and makes node behavior predictable. If you need multiple outputs, create multiple nodes. This constraint forces modular design and supports the node-centric philosophy.

### 6. Source Node Reactivation in Cycles (Forward Processing)

**Problem**: In cyclic graphs (e.g., `a->b->c->d->b`), source nodes like DataStreamNode never get reactivated because they have no predecessors to trigger them.

**Solution**: Automatic source node reactivation when needed by successors.

**Algorithm**:
```python
# When checking if successor is ready:
if successor has unprocessed predecessors:
    if any unprocessed predecessor is a source node (no predecessors):
        # Reactivate ALL source predecessors immediately
        add them to next_active list
        # Next iteration: sources compute, then successor can become ready

# Additionally, when no active nodes remain but unprocessed nodes exist:
for each unprocessed node:
    if ALL its unprocessed predecessors are source nodes:
        # Reactivate those source nodes
        # This handles cases where cycles prevent normal activation
```

**Example**:
```
Iteration 1: d processes, wants to activate b
             b has predecessor a (source, unprocessed)
             → a added to active list
Iteration 2: a processes (updates its DataStream value)
             → b now added to active list (all predecessors ready)
Iteration 3: b processes with updated value from a
```

**Limitation**: Nodes with circular dependencies on non-source nodes (e.g., `a->b->a` where neither is a source) cannot be resolved automatically. For such cases:
- Use ContainerNodes with initial values to break the cycle
- Include feedback nodes in `starting_nodes` to process them first
- Add a "warmup" iteration to initialize the cycle

**Key behavior**: 1-iteration delay for source reactivation, but uniform across network. Source nodes automatically update when their successors need them in cycles.

## Development Workflows

### Running Tests

```powershell
# Classic MLP (no graphs)
python ClassicMLPTestOnXOR.py

# Graph-based approaches
python CompareThreeApproaches.py  # Benchmarks all 3 modes

# Forward processing examples
python CompareForwardVsClassic.py

# Branch processing fix verification
python test_branch_processing_fix.py
```

### GUI Visual Testing

```powershell
# Launch GUI for visual testing
python run_gui.py
```

**Testing Forward Processing in GUI**:
1. Load example: Examples → Neural Networks → XOR Problem (2-2-1)
2. Set Processor Type: "Forward Processing"
3. Set Max Iterations: 500-1000 (or higher for convergence)
4. Click "Start" - should execute without errors
5. Observe: Active node highlighting, weight updates, loss decrease

**GUI Auto-Preparation**: The GUI automatically calls `mark_source_nodes_as_processed()` when:
- Loading a graph with forward processing enabled
- Switching to forward processing mode
- Resetting the graph

See `GUI_VISUAL_TEST_INSTRUCTIONS.md` for detailed testing procedures.

### GUI Development

```powershell
# Launch GUI (recently added - has known issues to be fixed)
python run_gui.py

# GUI is PyQt6-based, structure:
# - ComputationalGraphs/GUI/main_window.py: Main application
# - ComputationalGraphs/GUI/graph_canvas.py: Visual editor
# - ComputationalGraphs/GUI/node_palette.py: Node library
# - ComputationalGraphs/GUI/examples_loader.py: Pre-built examples
```

**GUI Keyboard Shortcuts**: Ctrl+M (generate MLP), Ctrl+B (add backprop), Ctrl+E (edit node), Delete (remove)

**Note**: GUI is in active development with known issues. Focus on core graph functionality for research validation before investing in GUI fixes.

### Adding New Node Types

1. Create node class in `ComputationalGraphs/Nodes/` inheriting from `Node`, `BasicNode`, or `AbstractNode`
2. Implement `Operation(self, *inputs)` method
3. For differentiable nodes, create derivative class (see `SigmoidNode` + `SigmoidDerivativeNode`)
4. Register in `ComputationalGraphs/GUI/node_palette.py` for GUI availability

Example pattern:
```python
class MyNode(BasicNode):
    def Operation(self, *inputs):
        # Your computation here
        return result

    derivative = MyNodeDerivative  # Link to derivative class
```

### Neural Network Construction

**Concurrent Mode** (with buffers):
```python
mlp = MLPGraph(numInputs=4, numOutputs=3, numHiddenLayers=2,
               hiddenLayerSizes=[5, 3], activationFunction=SigmoidNode)
mlp.BuildMLP()
backprop = BackpropGraph(mlp, learningRate=0.01)
backprop.BuildBackprop()

mlp.LoadData(X, y)  # X shape: (features, samples)
processor = GraphProcessor(mlp)
processor.ComputeGraph(iterations=1000)
```

**Forward Processing Mode** (no buffers):
```python
mlp = MLPGraphForwardProcessing(numInputs=4, numOutputs=3, ...)
mlp.BuildMLP()
backprop = BackpropGraphForwardProcessing(mlp, learningRate=0.01)
backprop.BuildBackprop()

mlp.LoadData(X, y)  # X shape: (samples, features) - different!
processor = GraphProcessor(mlp)
for epoch in range(epochs):
    processor.ForwardProcessing(iterations=iterations_per_epoch)
```

## Known Issues & Design Challenges


### Concurrent Mode Gradient Delay Problem (Revised)
After fixing the backpropagation connection issue, recent tests show that the gradient delay in concurrent mode is not a significant problem. The model can now achieve the second descent in the XOR problem, and buffer-induced delays do not prevent proper convergence. The previous belief that concurrent mode could not reach full learning curve descent was incorrect. Forward processing is still useful for buffer-free training, but concurrent mode is now validated for effective learning after the backprop fix.

### Forward Processing Branch Issue (SOLVED)
**Problem**: Starting nodes (first layer multiplication) need to access weight and input nodes that haven't been "processed" yet but already have values.

**Challenge**: After backprop is added, weight ContainerNodes have predecessors (dW gradient nodes), so they're not "source nodes" anymore, but they still need to provide initial values for the first forward pass.

**Solution**: Two-step preparation:
1. Mark all source nodes (no predecessors) as 'processed' - handles inputs, labels, learning rate
2. Mark all ContainerNodes as 'processed' even if they have predecessors - handles weights with initial values

```python
mlp = MLPGraphForwardProcessing(...)
mlp.BuildMLP()
mlp.LoadData(X, y)
backprop = BackpropGraphForwardProcessing(mlp, ...)
backprop.BuildBackprop()

processor = GraphProcessor(mlp)
mlp.PrepareForForwardProcessing(processor)  # Marks both source nodes AND ContainerNodes

# Now training works correctly
for epoch in range(epochs):
    processor.ForwardProcessing(iterations=iterations_per_epoch)
```

**Why this works**:
- Source nodes (DataStreamNodes) have loaded data and don't need computation
- Weight ContainerNodes have initial random values and don't need computation for first forward pass
- Marking both as 'processed' breaks the cycle: Forward pass (needs weights) → Backprop (computes gradients) → Weight update
- After the first forward pass, weights will be reactivated by their dW predecessors for gradient updates

### Common Pitfalls

1. **Forgetting `UpdateAdjacencyMatrix()`**: Always call after manual connections with `ConnectPreNode()`
2. **Buffer size miscalculation**: In concurrent mode, `(layersAhead * 6)` is critical - changing layer counts requires recalculating ALL buffer sizes
3. **Data shape confusion**: Row-per-feature (concurrent) vs row-per-sample (forward processing)
4. **Missing starting_nodes**: Weights MUST be in starting_nodes for forward processing (they have values and need gradient cycles)
5. **Threading overhead**: GraphProcessor auto-selects single-thread for <1000 nodes (Python GIL dominates)

## MLP Implementation Deep Dive

### Weight Naming Convention

**Critical for programmatic weight access and testing**:
- **Hidden layer weights**: `W_x{input}H0N{neuron}`
  - Example: `W_x0H0N1` = weight from input 0 to hidden layer 0, neuron 1
  - Pattern: `W_x{input_index}H{layer_index}N{neuron_index}`
- **Output layer weights**: `W_H0N{hidden}y{output}`
  - Example: `W_H0N1y0` = weight from hidden neuron 1 to output 0
  - Pattern: `W_H{layer_index}N{neuron_index}y{output_index}`

**Access pattern for weight manipulation**:
```python
for node in mlpGraph.nodes:
    if node.name.startswith("W_x") and "H0N" in node.name:
        input_idx = int(node.name[3])
        neuron_idx = int(node.name.split("H0N")[1])
        # Access/modify: node.value = new_weight
    elif node.name.startswith("W_H0N") and "y" in node.name:
        hidden_idx = int(node.name.split("W_H0N")[1].split("y")[0])
        output_idx = int(node.name.split("y")[1])
        # Access/modify: node.value = new_weight
```

### Weight Initialization Differences

**Critical for reproducible testing**:
- **MLPGraph** (concurrent): Uses Python's `random.uniform(-1, 1)` in `BuildMLP()` (line ~167)
- **ClassicMLP**: Uses NumPy's `np.random.uniform(-1, 1)`
- **Key insight**: `random.seed(42)` and `np.random.seed(42)` produce DIFFERENT random sequences
  - Even with identical seeds, the two generators diverge
  - Cannot achieve identical initialization by setting seeds alone

**Solution for identical initialization in testing**:
```python
# 1. Initialize ClassicMLP first, save weights BEFORE training
np.random.seed(42)
classic_mlp = ClassicMLP(input_size=2, hidden_size=2, output_size=1)
classic_initial_hidden = classic_mlp.weights[0].copy()  # Save before training
classic_initial_output = classic_mlp.weights[1].copy()

# 2. Build MLPGraph with its own seed
random.seed(42)
mlpGraph = MLPGraph(numInputs=2, numOutputs=1, numHiddenLayers=1,
                    hiddenLayerSizes=[2], ...)
mlpGraph.BuildMLP()

# 3. COPY Classic weights to MLPGraph BEFORE training
for node in mlpGraph.nodes:
    if node.name.startswith("W_x") and "H0N" in node.name:
        input_idx = int(node.name[3])
        neuron_idx = int(node.name.split("H0N")[1])
        node.value = classic_initial_hidden[input_idx, neuron_idx]
    elif node.name.startswith("W_H0N") and "y" in node.name:
        hidden_idx = int(node.name.split("W_H0N")[1].split("y")[0])
        output_idx = int(node.name.split("y")[1])
        node.value = classic_initial_output[hidden_idx, output_idx]
```

### Weight Storage Differences

**ClassicMLP** (numpy-based):
- Stored as list of numpy arrays: `weights[layer][input_idx, neuron_idx]`
- Layer 0 (hidden): Shape `(num_inputs, num_hidden_neurons)`
- Layer 1 (output): Shape `(num_hidden_neurons, num_outputs)`
- Access: `classic_mlp.weights[0][input, neuron]`

**MLPGraph** (node-based):
- Each weight is a separate `ContainerNode` with `node.value` attribute
- Must iterate through `mlpGraph.nodes` and parse names to access
- No layer-wise grouping - flat node list
- Access: Filter by name pattern, extract indices, read/write `node.value`

### Training Paradigm Differences

**ClassicMLP** (traditional batch/SGD):
- Configurable `batch_size` parameter (default 32)
- `batch_size=1` → Stochastic Gradient Descent (SGD)
  - Weight updates after EACH sample
  - Sequential processing: sample 1 → update → sample 2 → update
- `batch_size>1` → Mini-batch or full batch
  - Accumulate gradients across batch
  - Weight updates after ALL samples in batch processed

**MLPGraph** (concurrent parallel):
- ALL samples processed simultaneously in parallel streams
- DataStreamNodes emit values for all samples at once
- BufferNodes synchronize timing across network
- Weight updates occur after all samples have propagated
- Effectively equivalent to full-batch gradient descent
- Natural regularization from buffer delays allows higher learning rates

**Implication for testing**: Even with identical initialization, convergence patterns differ due to update timing. SGD (sequential) vs parallel batch produce different intermediate states, though both can achieve same final accuracy.

### Backpropagation Architecture Critical Fix

**Bug discovered**: Hidden layer error gradients (EG nodes) were not connected to learning rate multipliers (LRMult nodes).

**Location**: `BackpropGraph.py` line 77 (concurrent), similar pattern in forward processing version

**Before (BROKEN)**:
```python
lrMultNode.AddPreNode(self.lrNode)  # Missing gradient input!
```

**After (FIXED)**:
```python
lrMultNode.AddPreNode(hiddenErrorGradNode, self.lrNode)  # Gradient now flows
```

**Impact**: Without this connection, hidden layer gradients could not flow to weight updates. The network could only train output layer weights, severely limiting learning capacity. This was discovered through GUI visualization showing missing edges between EG and LRMult nodes.

**Testing verification**: After fix, concurrent MLPGraph achieves 100% accuracy on XOR problem (previously failed to converge).

## Project Structure

```
ComputationalGraphs/
├── Core/               # Graph execution engines
│   ├── Graph.py               # Base graph structure
│   ├── GraphProcessor.py      # Execution engine (concurrent/forward processing)
│   ├── MLPGraph.py            # MLP with buffers (concurrent)
│   ├── MLPGraphForwardProcessing.py  # MLP without buffers (forward processing)
│   ├── BackpropGraph.py       # Backprop with buffers
│   └── BackpropGraphForwardProcessing.py  # Backprop without buffers
├── Nodes/              # 35+ node types (arithmetic, activation, EA, fuzzy, etc.)
├── GUI/                # PyQt6 visual editor
└── Examples/           # Pre-built demonstration graphs

# Root-level test files: Classic*, Compare*, Test*
```

## Documentation References

- `ARCHITECTURE_COMPARISON.md`: Deep dive into concurrent vs forward processing execution
- `GUI_README.md`: Visual editor usage and features
- `EXAMPLES_FEATURES.md`: Pre-built examples and automation tools
- `PLOTTING_FEATURE.md`: Real-time visualization capabilities

## Model Hybridization Approach

The framework's unified graph representation enables unprecedented model hybridization:

**Example hybrid possibilities**:
- Fuzzy logic preprocessing → Neural network → Evolutionary algorithm optimization
- Neural network with fuzzy activation functions
- Evolutionary algorithm-driven neural architecture search in the same graph

**Implementation pattern**:
```python
# Create components from different model families
fuzzy_preprocessor = Graph()  # Build fuzzy logic nodes
mlp = MLPGraphForwardProcessing(...)  # Neural network
ea_optimizer = Graph()  # Evolutionary algorithm nodes

# Connect across model boundaries - the key insight
unified_graph = Graph()
unified_graph.AddNode(*fuzzy_preprocessor.nodes)
unified_graph.AddNode(*mlp.nodes)
unified_graph.ConnectPreNode(mlp.inputLayer[0], fuzzy_preprocessor.outputNode)
unified_graph.UpdateAdjacencyMatrix()
```

All model types are just nodes - connections define the hybrid architecture.

### Fusion-Level Hybridization (author's definition)

- Fusion hybrid AI modifies a model's micro-architecture (internal ops or components) to create a hybrid model (example: ANFIS). This differs from hierarchical/network hybridization where whole models are composed without changing their internals. Fusion typically requires reimplementation of internal parts (hardest form of hybridization).
- The ComputationalGraphs framework is intentionally node-centric to make fusion easy: swap or extend node-level micro-ops (activations, membership functions, message functions) to create fusion hybrids without touching unrelated nodes. When implementing fusion, prefer adding new nodes and wiring them into graphs; do NOT change existing fuzzy-system nodes directly (keep tests stable).


## Performance Notes

- Single-thread often faster than multi-thread for <1000 nodes due to Python GIL
- GraphProcessor auto-selects optimal threading mode
- **Concurrent mode**: All samples in parallel streams (complex system simulation)
- **Forward processing**: Samples sequential, but eliminates gradient delay (better for training)
- Trade-off: Concurrent enables emergence, Forward enables convergence

# Architecture Comparison: MLPGraph (Concurrent) vs MLPGraphForwardProcessing

Zorvan builds MLPs out of nodes in two variants, one for each processing mode:

- **`MLPGraph` / `BackpropGraph`**: concurrent processing, the main and
  validated mode. Every tick, all nodes read a snapshot of the graph and then
  update, so a signal advances one node per tick. Buffers and label delays line
  the signals up.
- **`MLPGraphForwardProcessing` / `BackpropGraphForwardProcessing`**: forward
  processing (experimental). Nodes run along data dependencies, so no buffers
  are needed.

## Key Architectural Differences

### 1. **Buffer Nodes**

**MLPGraph (Concurrent):**
- Has BufferNodes after every layer:
  - Input layer: `(DataStreamNode, BufferNode)` pairs
  - Hidden layers: `(AdditionNode, ActivationNode, BufferNode)` triplets
- Buffers keep past values so backprop can use the values from the tick a
  sample actually passed through the layer.

**MLPGraphForwardProcessing:**
- Input layer: `DataStreamNode` only
- Hidden layers: `(AdditionNode, ActivationNode)` pairs only
- Direct propagation without buffering

**Impact:** buffers make concurrent training possible. Their cost is that
weight updates are delayed by the buffer depth (stale gradients), so a
concurrent MLP behaves like classic backprop but is not mathematically identical
to it.

---

### 2. **Input Layer**

**MLPGraph (Concurrent):**
```python
self.inputLayer = [(DataStreamNode(name=f"x{i}"),
                    BufferNode(name=f"Buff_x{i}", size=((self.numHiddenLayers + 1) * 6)))
                   for i in range(self.numInputs)]
```
- DataStreamNode + BufferNode pairs
- The buffer stores input values for delayed use by backprop

**MLPGraphForwardProcessing:**
```python
DataStreamNode(name=f"x{i}", initialDelay=0, streamDelay=0)
```
- DataStreamNode only (no buffer)
- `initialDelay=0, streamDelay=0` for immediate streaming
- Direct connections to multiplication nodes

**Impact:** in forward processing, inputs feed computations directly as nodes
become active.

---

### 3. **Hidden Layers**

**MLPGraph (Concurrent):**
```python
layersAhead = (self.numHiddenLayers + 2) - (layerNum + 2)
bufferNode = BufferNode(name=f"Buff_H{layerNum}N{i}", size=(layersAhead * 6))
hiddenLayer.append((additionNode, activationNode, bufferNode))
```
- 3-tuple: Addition + Activation + Buffer
- Buffer size depends on how many layers lie ahead
- Activation functions can differ per layer (`hiddenActivationFunctions`)

**MLPGraphForwardProcessing:**
```python
hiddenLayer.append((additionNode, activationNode))
```
- 2-tuple: Addition + Activation only (no buffer)
- Activation output connects directly to the next layer

---

### 4. **Label Layer**

**MLPGraph (Concurrent):**
```python
labelLayerDelay = (self.numHiddenLayers + 1) * 3
self.labelLayer = [DataStreamNode(name=f"L_y{i}", initialDelay=labelLayerDelay)
                   for i in range(self.numOutputs)]
```
- `initialDelay` makes labels arrive when the matching outputs do

**MLPGraphForwardProcessing:**
```python
DataStreamNode(name=f"L_y{i}", initialDelay=0, streamDelay=0)
```
- No synchronization delay needed

**Impact:** concurrent mode needs delay calculations; forward processing
doesn't. (The planned engine replaces hand-computed delays with delay edges
plus automatic delay balancing; see `docs/REARCHITECTURE_PLAN.md`.)

---

### 5. **Weight Layers**

**Both architectures:**
- Use `ContainerNode` for weights
- Initialize with `random.uniform(-1, 1)` unless an initializer is given
- Same structure: weights connect every pair of nodes in adjacent layers

---

### 6. **Starting Nodes**

**MLPGraph (Concurrent):**
```python
for input_buffer_pair in self.inputLayer:
    self.starting_nodes.append(input_buffer_pair[0])  # DataStreamNode only
for label_node in self.labelLayer:
    self.starting_nodes.append(label_node)
# Does NOT include weights
```

**MLPGraphForwardProcessing:**
```python
self.starting_nodes = self.firstLayerMultNodes
# Before training: mlp.PrepareForForwardProcessing(processor)
# marks source nodes (inputs, labels, learning rate) and all ContainerNodes
# (weights) as already processed, so the first multiplications can read them.
```

**Impact:** forward processing starts at the first *operations* and relies on
the preparation step to make data and weights available.

---

### 7. **Data Loading**

**MLPGraph (Concurrent):**
```python
def LoadData(self, X, y):
    # X = [[all_x0_values], [all_x1_values], ...] (row-per-feature)
    # y = [[all_y0_values], [all_y1_values], ...] (row-per-output)
```
- Data format: **rows are features**, columns are samples
- Example: `X = [[0,0,1,1], [0,1,0,1]]` for 4 samples of 2 features

**MLPGraphForwardProcessing:**
```python
def LoadData(self, X_data, y_data):
    # X_data = [[x0, x1], [x0, x1], ...] (row-per-sample)
    # y_data = [[y0], [y0], ...] (row-per-sample)
```
- Data format: **rows are samples**, columns are features
- Example: `X = [[0,0], [0,1], [1,0], [1,1]]` for 4 samples of 2 features
- **Transposes internally** to match DataStreamNode expectations

**Impact:** the two classes expect different input layouts.

---

### 8. **Execution Model**

**MLPGraph (Concurrent):**
```python
processor.ComputeGraph(totalIterations + 1)
```
- Single continuous execution
- All nodes process every tick from the same snapshot
- Buffers synchronize data flow
- Samples stream through the network in a pipeline

**MLPGraphForwardProcessing:**
```python
for epoch in range(epochs):
    processor.ForwardProcessing(iterations=iterations_per_epoch)
```
- Replays a precomputed dependency-ordered sequence
- No buffering, immediate propagation
- Samples processed one at a time

---

## Summary Table

| Feature | MLPGraph (Concurrent) | MLPGraphForwardProcessing |
|---------|----------------------|---------------------------|
| **Mode status** | Main, validated | Experimental |
| **Buffers** | After every layer | None |
| **Input Layer** | DataStream + Buffer pairs | DataStream only |
| **Hidden Layers** | (Add, Act, Buffer) | (Add, Act) |
| **Label Delays** | Calculated sync delays | No delays (0, 0) |
| **Starting Nodes** | Inputs + Labels | First-layer multiplications (sources and weights pre-marked as processed) |
| **Data Format** | Rows = features | Rows = samples (transposed internally) |
| **Processing** | All nodes every tick (snapshot) | Dependency-ordered sequence |
| **Synchronization** | Buffers + delays | Execution order |
| **Weight updates** | Delayed by buffer depth | Immediate |

---

## Known Issues & Design Notes

### Concurrent Mode Gradient Delay
After the backpropagation wiring fix (hidden-layer error gradients connected to
their learning-rate multipliers), the gradient delay in concurrent mode turned
out not to be a significant problem. The concurrent MLP reaches the second
descent on XOR, and buffer delays don't prevent convergence. They do make
training more sensitive to the learning rate. Forward processing remains useful
for buffer-free training.

---

## Hybridization Vocabulary

- **Fusion hybrid:** changes a model's micro-architecture: its internal
  operations or structure (for example ANFIS, or an MLP layer mixing sigmoid,
  tanh and ReLU neurons). Traditionally the hardest kind of hybrid, because it
  usually requires reimplementing parts of the models.
- **Modular hybrid:** whole models cooperate without changing their internals,
  either hierarchically (one model's output feeds another) or as a network
  (ensembles, interacting modules). The main risk is hidden dependencies that
  only show up during implementation.
- **How Zorvan supports both:** every micro-operation is a node, so fusion means
  rewiring or swapping nodes (activations, membership functions, operators)
  rather than reimplementing a model. Modular composition means connecting
  subgraphs, and the visual graph makes dependencies explicit. Examples in this
  repository: `MLPAnfisGraph` / `BackpropAnfisGraph` (ANFIS XOR example in the
  GUI) and per-layer activations via `MLPGraph(hiddenActivationFunctions=...)`.
  Mixing activations *within* a layer is done by wiring activation nodes
  directly.

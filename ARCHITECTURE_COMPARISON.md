# Architecture Comparison: MLPGraph (Concurrent) vs MLPGraphForwardProcessing

## Key Architectural Differences

### 1. **Buffer Nodes**

**MLPGraph (Concurrent):**
- ✅ Has BufferNodes after EVERY layer:
  - Input layer: `(DataStreamNode, BufferNode)` pairs
  - Hidden layers: `(AdditionNode, ActivationNode, BufferNode)` triplets
  - Buffer sizes calculated based on layers ahead: `(layersAhead * 6)`
  
**MLPGraphForwardProcessing:**
- ❌ NO BufferNodes anywhere
  - Input layer: `DataStreamNode` only
  - Hidden layers: `(AdditionNode, ActivationNode)` pairs only
  - Direct propagation without buffering

**Impact:** Buffers allow concurrent processing by storing values for later use. Without buffers, values propagate immediately through active node processing.

---

### 2. **Input Layer**

**MLPGraph (Concurrent):**
```python
self.inputLayer = [(DataStreamNode(name=f"x{i}"), 
                    BufferNode(name=f"Buff_x{i}", size=((self.numHiddenLayers + 1) * 6))) 
                   for i in range(self.numInputs)]
```
- DataStreamNode + BufferNode pairs
- Buffer stores input values for delayed processing

**MLPGraphForwardProcessing:**
```python
self.inputLayer = [DataStreamNode(name=f"x{i}", initialDelay=0, streamDelay=0) 
                  for i in range(self.numInputs)]
```
- DataStreamNode only (no buffer)
- `initialDelay=0, streamDelay=0` for immediate streaming
- Direct connections to multiplication nodes

**Impact:** ForwardProcessing inputs feed directly into computations as nodes become active.

---

### 3. **Hidden Layers**

**MLPGraph (Concurrent):**
```python
hiddenLayer.append((additionNode, activationNode, bufferNode))
```
- 3-tuple: Addition + Activation + Buffer
- Buffer stores activated output for later layers

**MLPGraphForwardProcessing:**
```python
hiddenLayer.append((additionNode, activationNode))
```
- 2-tuple: Addition + Activation only (no buffer)
- Activation output connects directly to next layer

**Impact:** ForwardProcessing has immediate propagation through layers.

---

### 4. **Label Layer**

**MLPGraph (Concurrent):**
```python
labelLayerDelay = ((self.numHiddenLayers + 1) * 3)
self.labelLayer = [DataStreamNode(name=f"L_y{i}", initialDelay=labelLayerDelay) 
                  for i in range(self.numOutputs)]
```
- Has `initialDelay` to synchronize with output arrival time
- Delays streaming to match when outputs are ready

**MLPGraphForwardProcessing:**
```python
self.labelLayer = [DataStreamNode(name=f"Label_y{i}", initialDelay=0, streamDelay=0) 
                  for i in range(self.numOutputs)]
```
- `initialDelay=0, streamDelay=0` - no synchronization needed
- Labels available immediately (forward processing handles timing through active node propagation)

**Impact:** Concurrent needs delay calculation for synchronization; ForwardProcessing doesn't.

---

### 5. **Weight Layers**

**Both architectures:**
- Both use `ContainerNode` for weights ✅
- Both initialize with `random.uniform(-1, 1)` ✅
- Same structure: 2D arrays connecting layers ✅

**No difference** - weights are identical in both!

---

### 6. **Starting Nodes**

**MLPGraph (Concurrent):**
```python
for input_buffer_pair in self.inputLayer:
    self.starting_nodes.append(input_buffer_pair[0])  # DataStreamNode only
for label_node in self.labelLayer:
    self.starting_nodes.append(label_node)  # DynamicDataStreamNode
# Does NOT include weights
```

**MLPGraphForwardProcessing:**
```python
self.starting_nodes = (
    self.inputLayer +           # Input DataStreamNodes
    self.labelLayer +           # Label DataStreamNodes
    all_weight_nodes           # ALL weight ContainerNodes
)
```

**Impact:** ForwardProcessing includes weights in starting_nodes because they need to be active from the start (they have values and cycles for gradient updates).

---

### 7. **Data Loading**

**MLPGraph (Concurrent):**
```python
def LoadData(self, X, y):
    # X = [[all_x0_values], [all_x1_values], ...] (row-per-feature)
    # y = [[all_y0_values], [all_y1_values], ...] (row-per-output)
    for i in range(self.numInputs):
        self.inputLayer[i][0].data = X[i]  # Load into DataStreamNode
    for i in range(self.numOutputs):
        self.labelLayer[i].data = y[i]
```
- Data format: **rows are features**, columns are samples
- Example: `X = [[0,0,1,1], [0,1,0,1]]` for 4 samples of 2 features

**MLPGraphForwardProcessing:**
```python
def LoadData(self, X_data, y_data):
    # X_data = [[x0, x1], [x0, x1], ...] (row-per-sample)
    # y_data = [[y0], [y0], ...] (row-per-sample)
    for i in range(self.numInputs):
        feature_column = [sample[i] for sample in X_data]  # Extract column
        self.inputLayer[i].data = feature_column
```
- Data format: **rows are samples**, columns are features
- Example: `X = [[0,0], [0,1], [1,0], [1,1]]` for 4 samples of 2 features
- **Transposes internally** to match DataStreamNode expectations

**Impact:** Different input formats! MLPGraph expects transposed data.

---

### 8. **Execution Model**

**MLPGraph (Concurrent):**
```python
mlpProcessor.ComputeGraph(totalIterations + 1)
```
- Single continuous execution
- All nodes process every iteration (concurrent)
- Buffers synchronize data flow
- All samples processed in parallel streams

**MLPGraphForwardProcessing:**
```python
for epoch in range(epochs):
    processor.ForwardProcessing(iterations=iterations_per_epoch)
```
- Active node execution (only nodes with completed predecessors)
- Nodes only process when active (all predecessors done)
- No buffering - immediate propagation
- Samples processed sequentially (one sample at a time through active node propagation)

---

## Summary Table

| Feature | MLPGraph (Concurrent) | MLPGraphForwardProcessing |
|---------|----------------------|---------------------------|
| **Buffers** | ✅ After every layer | ❌ None |
| **Input Layer** | DataStream + Buffer pairs | DataStream only |
| **Hidden Layers** | (Add, Act, Buffer) | (Add, Act) |
| **Label Delays** | Calculated sync delays | No delays (0, 0) |
| **Starting Nodes** | Inputs + Labels | Inputs + Labels + **Weights** |
| **Data Format** | Rows=features | Rows=samples (transposed internally) |
| **Processing** | Concurrent (all nodes) | Active nodes only (when predecessors complete) |
| **Synchronization** | Via buffers + delays | Via active node propagation |

---

## Why Weights Work in Concurrent but Not in ForwardProcessing?

**Hypothesis:**
1. In **Concurrent**, weights are processed every iteration but buffers prevent immediate propagation
2. In **ForwardProcessing**, weights are in starting_nodes so they're active from the first iteration
3. BUT: If weights aren't being updated properly, or if they're accumulating incorrectly...

**Need to investigate:**
- Are weight updates (gradient applications) happening correctly?
- Are ContainerNodes accumulating properly in ForwardProcessing?
- Is the backprop graph structured correctly for forward processing execution?

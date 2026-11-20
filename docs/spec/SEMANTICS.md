# Concurrent processing semantics

Status: **Accepted Phase 0 baseline** · Reference: current Python implementation

This document records the observable behavior the Rust engine must reproduce.
It is a working specification, not a claim that every reference node already
follows the desired design. Known gaps are called out explicitly.

## Graph and values

A graph contains nodes and directed connections. Each node has a value; the
value domain is open and may include numbers, booleans, strings, lists, arrays,
or other serializable application data. A connection from `u` to `v` makes `u`
a predecessor of `v`. A node's predecessor list is ordered by connection
insertion order. Self-connections and cycles are permitted.

Basic nodes receive an ordered list of valid predecessor values. In the Python
reference, `BasicNode.UpdateInputs()` calls `IsValidInput` on each predecessor
value and drops values that fail. An abstract predecessor is flattened one
level: its member values are considered in member order and are filtered the
same way. Thus filtering can change both input count and batch boundaries.

The intended node contract is a deterministic procedure
`Operation(inputs, t) -> value`. The current `Operation` methods generally do
not receive `t`; time-dependent nodes may keep private counters. `DataStreamNode`
and `DynamicDataStreamNode` do this today. `MutationNode` uses Python's global
random generator. These are reference limitations to resolve before claiming
cross-run or cross-thread determinism.

## Concurrent tick

`GraphProcessor.ComputeGraph` executes each tick in two phases:

1. **Snapshot inputs.** For each top-level node that is not
   `midCalculation`, call `UpdateInputs()`. A complex node snapshots each
   eligible internal node as well. Inputs are copied as values in predecessor
   order.
2. **Process.** Call `ProcessBatch()` for every top-level node, including nodes
   that were skipped in Phase 1 because they were mid-calculation. Complex
   nodes process their internal nodes from the inputs captured in Phase 1.

The single-threaded processor visits graph order within each phase. The
multi-threaded processor waits for all Phase 1 chunks before Phase 2 and waits
for all Phase 2 chunks before advancing. A node does not wait for its
predecessors to compute during the current tick. Therefore a path of `k` nodes
propagates a changed source value through up to `k` ticks. Correctly isolated
nodes should have results independent of graph iteration order.

The processor increments its `time` once per completed tick. The current node
API does not pass this value to `Operation`, so it is not generally available
to node logic.

## Batches and postponement

`Node.ProcessBatch()` uses `batchSize`, `inclusive`,
`forcedBatchProcessing`, `midCalculation`, and `midCalculationValue`:

- A node with fewer than `batchSize` values cannot start an operation. It
  postpones computation and retains its previous public value, except for
  node-specific behavior that explicitly changes it.
- A batch contains the first `batchSize` pending values. Remaining values are
  retained for later processing.
- With `inclusive=True`, the current running result is prepended to a later
  batch while a calculation spans ticks. With `inclusive=False`, later batches
  are passed without that accumulated value.
- With `forcedBatchProcessing=True`, batches are consumed repeatedly in the
  same `ProcessBatch()` call. Otherwise, processing can span ticks and the
  node's `midCalculation` flag is used by the next tick's snapshot phase.
- An incomplete first batch leaves the old public value unchanged. If a
  calculation is already in progress and an exclusive (`inclusive=False`)
  final remainder is smaller than `batchSize`, the base implementation ends
  the calculation, publishes the previous `midCalculationValue`, and drops
  that remainder. Inclusive processing prepends the running result, so the
  final remainder may complete a batch. `AdditionNode` and `DivisionNode`
  also special-case a lone input when no calculation is in progress.
- `user_locked_value` prevents selected writes to the public `value`; internal
  batch state may still advance.

The precise edge cases for an incomplete final batch, zero inputs, exceptions,
and node-specific overrides must be captured in conformance cases. The base
implementation is in `reference/zorvan_reference/Nodes/Node.py`.

## Complex nodes

`CompressedNode` is an ordered view over a chain. Its internal nodes snapshot
and process one tick at a time; it must not collapse chain latency. Its public
value mirrors the last internal node. Direct `Operation()` calls on a
`CompressedNode` evaluate the chain as a one-shot operation and are not
equivalent to running it through a processor.

`AbstractNode` is a view over an ordered list of parallel internal nodes. Its
value is the list of member values. Processor execution snapshots each member
before processing members. Direct `Operation()` is a separate one-shot path.

Compression and abstraction are intended to preserve processor traces. The
regression test is `reference/Tests/core/graph/test_complex_node_snapshot_semantics.py`.
“Trace-equivalent” means every externally observed node has the same value at
each tick. “Delay-equivalent” means those sequences match after a fixed,
per-node shift. No processor optimization may silently trade one for the other.

## Other processors

`ManualProcessing` processes the configured starting-node group followed by
each configured sequence group, one group per call iteration. For each group,
it snapshots eligible inputs and then processes that group. Nodes outside the
current group do not run. `find_execution_sequence()` constructs a dependency
sequence; it is a helper and does not itself execute nodes.

Forward processing is experimental. Its readiness and cycle behavior must be
specified with dedicated conformance cases before it is treated as stable.

## State and reset

`ResetValue()` on a `BasicNode` sets `value` to zero unless
`user_locked_value=True`. It does not define a universal reset for every
subclass's private state. `BufferNode`, `SequencerNode`, stream nodes, and
batch-processing fields therefore need explicit per-kind reset rules.

The current special-node behavior is:

- **`DataStreamNode`.** Construction starts at `data[0]` (or `None`) with
  `iteration=0`, `lastStream=0`, and `streamIndex=0`. Each `ProcessBatch()` may
  emit only when `initialDelay - iteration <= 0` and
  `iteration - lastStream >= streamDelay`. On emission it increments the
  index before reading, wraps to index zero at the end, and updates
  `lastStream`; it increments `iteration` on every call. Thus, with both
  delays zero, the first processing tick emits `data[1]` (or `data[0]` for a
  one-element stream). Empty `data` raises when emission is attempted.
  `ResetValue()` resets counters but sets `data=None` and does not reset the
  published value; subsequent processing can fail.
- **`DynamicDataStreamNode`.** Its `Operation(input)` appends non-`None` input
  to `data` and uses the same counter/index rules. Its current
  `IsValidInput()` returns `None`, which filters every predecessor value in
  `BasicNode.UpdateInputs()`, so ordinary processor execution does not deliver
  those values to `Operation`. Its constructor also uses a mutable empty-list
  default. `ResetValue()` sets `data=None` and resets counters.
- **`BufferNode`.** Construction copies `data`, or creates `[None] * size`, and
  sets `bufferSize=max(size, len(buffer))`; its value starts as the first
  buffer item. Each operation deep-copies and appends an input, removes the
  oldest item if over capacity, and publishes the oldest remaining item. With
  `allowNone=False`, `None` is not appended and output selects the first
  non-`None` item. `ResetValue()` and `ResetBuffer()` clear the private buffer
  and publish `None` unless user-locked.
- **`SequencerNode`.** Its private queue is separate from `value`. Each
  operation first removes one queued item when not mid-calculation, then
  appends a non-`None` input (a list of lists is extended as multiple items),
  then publishes the new first item. Consequently, the first item in initial
  data is removed on the first operation. `ResetValue()` clears the queue and
  publishes zero unless user-locked; `ResetBuffer()` clears it and publishes
  `None` unless user-locked.

These rules describe current behavior, including defects. They are not a
decision to preserve the defects in the Rust engine; any fix that changes a
trace needs an explicit decision-log entry and updated conformance cases.

## Cycles and determinism

A self-loop is an ordinary predecessor edge. Concurrent processing snapshots
the node's value before any node computes, so a self-loop reads that node's
previous-tick value. Cycles are permitted and run without topological waiting.
`Graph.AddPreNode()` avoids adding the same predecessor object twice, so the
Python reference does not represent parallel identical edges through that
API.

Processor-based `AbstractNode.ProcessBatch()` visits independent members
sequentially after snapshotting them. Direct calls to `AbstractNode.Operation()`
still create a thread pool. Population initialization, crossover, tournament,
and mutation nodes use global Python `random`; some initializers use NumPy's
global random state. Their output can depend on unrelated random calls and is
not keyed by node or tick. A fixed process seed can reproduce a case, but does
not make parallel execution schedule-independent.

The desired model keeps semantic memory in a node's value and reads it through
a self-loop; time-driven behavior uses the tick number; random behavior uses a
counter-based source keyed by seed, node identity, and tick. This is a target
constraint, not current reference behavior. No global semantic change is made
by this document.

## Simplification constraints

Complex nodes are views over the flat graph. Simplification must preserve the
per-tick trace and must not execute a chain in one tick. Node splitting is
restricted to acyclic graphs by `simplify_fully`; nodes on cycles must not be
split because repeated splitting may fail to terminate. Any future relaxation
requires a termination argument and conformance coverage.

## Conformance requirements

Each case records a graph, inputs or initial values, processor mode, tick
count, and the value of every node after each tick. Floating-point comparisons
must declare absolute and relative tolerances; non-numeric values compare
structurally and exactly. Cases should cover each node kind, ordered and
filtered inputs, batch boundaries, locked values, cycles, complex-node views,
streams, buffers, manual execution, and representative end-to-end models.

## Known decisions still needed

- Whether filtering invalid inputs is retained as part of the contract or
  replaced by optional type constraints.
- Whether stream counters become functions of processor time, including the
  exact `initialDelay` and `streamDelay` boundary behavior.
- The exact state/reset semantics of buffer and sequencer nodes.
- Determinism requirements and seeding for evolutionary/random nodes.
- Formal behavior for exceptions raised by a node operation.

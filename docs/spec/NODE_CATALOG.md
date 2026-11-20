# Python reference node catalog

Status: **Accepted Phase 0 inventory** · Input positions are predecessor order after
`IsValidInput` filtering. Parameters and state names below refer to the Python
implementation; custom GUI nodes are user-defined and are not enumerable here.

Every `BasicNode` operation receives its positional input arguments in this
order. Nodes inherit batching fields from `Node`: `batchSize`, `inclusive`,
`forcedBatchProcessing`, `midCalculation`, and `midCalculationValue`. Their
defaults can be overridden by each kind. `value` is the published output.
`user_locked_value` suppresses writes in the base processor and reset path.

## Structural node kinds

| Kind | Inputs and output | Parameters / state | Valid inputs |
|---|---|---|---|
| `CompressedNode` | Ordered chain; external inputs route to first member, output mirrors last member. | Ordered `nodes`; member states remain distinct. | Members apply their own validation. |
| `AbstractNode` | Parallel member nodes; each member reads its own predecessors; output is ordered list of member values. | Ordered `nodes`; member states remain distinct. | Members apply their own validation. |

## Core, activation, and utility nodes

| Kind | Ordered operation inputs | Parameters / state | Accepted inputs / operation |
|---|---|---|---|
| `AdditionNode` | `a, b` per batch | `batchSize=2`, inclusive accumulation | Numeric (Python and NumPy numeric values); adds. |
| `SubtractionNode` | `a, b` | `batchSize=2`, inclusive accumulation | Numeric; subtracts in position order. |
| `MultiplicationNode` | `a, b` | `batchSize=2` | Numeric; multiplies. |
| `DivisionNode` | `a, b` | `batchSize=2`, inclusive accumulation | Numeric; divides in position order; denominator edge cases follow Python operation. |
| `MinNode` | `a, b` batches | `forcedBatchProcessing=True` | Numeric; minimum. |
| `MaxNode` | `a, b` batches | `forcedBatchProcessing=True` | Numeric; maximum. |
| `ContainerNode` | `i` | `value`, `Incremental`; `batchSize=1` | Numeric; adds `i` when incremental, otherwise subtracts it from current value. |
| `InitializableContainerNode` | Inherits container | Initialization configuration | Inherits numeric validation and container operation. |
| `DisplayNode` | `input` | Display value and standard batch fields | Source documents validation as subclass-defined; emits/records the input. |
| `LinearNode` | `input` | `value`, slope/intercept configuration | Numeric validation; linear transform. |
| `LinearNodeDerivative` | `input` | `value` | Numeric derivative operation. |
| `SigmoidNode` | `x` | `value` | Numeric; sigmoid. |
| `SigmoidDerivativeNode` | `sigmoid_output` | `value` | Numeric; sigmoid derivative from output. |
| `TanhNode` | `x` | `value` | Numeric; hyperbolic tangent. |
| `TanhDerivativeNode` | `tanh_output` | `value` | Numeric; tanh derivative from output. |
| `ReLUNode` | `x` | `value` | Python `int` or `float`; rectified linear operation. |
| `ReLUDerivativeNode` | `ReLUOutput` | `value` | Numeric; derivative from activation output. |
| `GaussianNode` | `input_value` | `mean`, `sigma`, `amplitude` | Real number; Gaussian operation. |
| `PiecewiseLinearNode` | `x` | `xs`, `mus` | Python/NumPy integer or floating scalar; piecewise interpolation. |
| `ListNode` | `input` | `allowNone`, forced batching | Any; accumulates list entries. |
| `ExtractListElement` | `input` | Index/configuration in node fields | List-like input; selects configured element. |
| `TrimListNode` | `input` | `max_len` | Any; trims list to configured limit. |
| `MeanSquaredNode` | `input` | Inherited buffer fields and `mode` | Inherits buffer validation; rolling mean-square behavior. |
| `MeanSquaredErrorNode` | `input` | Inherited buffer fields and `mode` | Inherits buffer validation; current implementation also computes the mean square relative to zero. |

## Streams and memory

| Kind | Ordered operation inputs | Parameters / state | Accepted inputs / operation |
|---|---|---|---|
| `DataStreamNode` | No inputs | `data`, `initialDelay`, `streamDelay`, private `iteration`, `lastStream`, `streamIndex` | Emits cyclic data values on its private counter. Its `IsValidInput` currently returns `None`; not used for its own source output. |
| `DynamicDataStreamNode` | `input` | Same stream fields plus mutable `data` | `IsValidInput` currently returns `None`; appends non-`None` inputs, then emits by private counter. |
| `BufferNode` | `input` | Separate `buffer`, `bufferSize`, `allowNone` | Any; maintains bounded history and publishes oldest permitted item. |
| `SequencerNode` | `input` | Separate `buffer`; forced batching | Any; queues incoming items and emits first item. A list-of-lists input is expanded into the queue. |
| `MovingAverageNode` | `input` | Inherits `BufferNode` history and size; mode | Inherits buffer validation; publishes average of buffered values. |

## Fuzzy nodes

| Kind | Ordered operation inputs | Parameters / state | Accepted inputs / operation |
|---|---|---|---|
| `GaussianMembershipNode` | `x, c, s` | `default_center`, `default_sigma` | Numeric; Gaussian membership. |
| `GaussianCenterDerivativeNode` | `x, c, s` | None beyond base state | Numeric; membership derivative with respect to center. |
| `GaussianSigmaDerivativeNode` | `x, c, s` | None beyond base state | Numeric; membership derivative with respect to sigma. |

## Evolutionary nodes

| Kind | Ordered operation inputs | Parameters / state | Accepted inputs / operation |
|---|---|---|---|
| `PopulationNode` | Inherits buffer input | `genome_length`, bounds, generation flag; random initial population | Individuals are list values; initialization uses Python global `random`. |
| `TournamentSelectionNode` | `candidate, fitness` | `tournamentSize` | Candidate/fitness pair; tournament selection. |
| `BulkTournamentNode` | `candidate, fitness` | `tournamentSize`, `populationSize`, `num_selections` | Numeric fitness and candidate data; bulk tournament selection. |
| `CrossoverNode` | `p1, p2` | `rate`, `delay`; subclass operation | Parent values; base validity is subclass-defined. |
| `SingleCrossoverNode` | `p1, p2` | Base node fields | Parent values; single-point crossover. |
| `SingleInputCrossover` | `input` | Crossover configuration and batch fields | Parent/list data; single-input crossover operation. |
| `MutaionNode` | `inp` | `rate`, `scale` | Any; mutation uses Python global `random`. The class name is misspelled in the reference. |
| `ElitismNode` | `individual, fitness` | `population_size`, `num_elites` | Any pair; preserves configured elite count. |
| `BestFitnessTrackerNode` | `individual, fitness` | `population_size` | Any pair; tracks best fitness/individual. |
| `DeJongSphereNode` | `input` | None beyond base state | List of numeric values; evaluates sphere objective. |

## Initializers

`UniformInitializer` and `NormalInitializer` in `reference/zorvan_reference/Nodes/Initializers/`
are helper objects rather than graph node kinds. They configure initial values
for consuming nodes; their randomness currently follows NumPy/Python library
global RNG behavior. Their seed contract is not yet standardized.

## Catalog limitations to resolve

This inventory is derived from source signatures and needs executable
conformance coverage before becoming the stable Rust node schema. Some nodes
have custom `ProcessBatch()` behavior, and several `IsValidInput()` methods
have implementation defects or permissive behavior. Preserve current
observable behavior in the reference cases; record any deliberate fixes in the
decision log before changing semantics. GUI-defined custom nodes need a
separate plugin schema and cannot be listed by this static catalog.

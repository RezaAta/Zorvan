# Zorvan Re-architecture Plan

Status: **Draft, agreed direction** · Created: 2026-11-17 · Owner: project lead

This document is the plan for moving Zorvan from a pure-Python prototype to a
Rust engine with multiple clients. It records *what* we will build, *why*, in
*what order*, and *how we know each phase is done*. Update the status table and
the decision log as work progresses, and don't delete superseded decisions; mark them.

---

## 1. Vision and principles

**Core idea.** Every AI model can be expressed as a computational graph. That makes
it easier to search the space of architectures, combine models below the
whole-model level without reimplementing them, and understand models visually.

**Product goals**
1. A general visual tool that lets AI scientists build hybrid systems.
2. A platform for designing search methods that generate hybrid AI
   architectures.

**Principles that constrain every design decision**

| # | Principle | Consequence |
|---|-----------|-------------|
| P1 | **The node is the unit of meaning.** | We make things faster by changing how nodes are stored and run, not by turning models into matrices. Tensor-valued nodes are optional and never required. |
| P2 | **Smarter nodes over bigger models.** | Node kinds must be extensible (Rust, Python, WASM) and may carry state and logic. |
| P3 | **Wiring freedom is a feature.** | Inputs stay ordered and untyped by default, so fully random rewiring stays possible for search. Types are *optional* constraints. |
| P4 | **The processing sequence is first-class.** | An algorithm = data + process + processing sequence. Schedulers are pluggable, and a sequence can be derived (concurrent/forward), listed (manual) or computed (programmable). |
| P5 | **One engine, many places.** | The same engine runs inside the desktop app, in the browser (WASM) and on cloud workers. Clients only see an "engine endpoint". |
| P6 | **Offline is complete; the cloud is for scale.** | Every feature works offline. The cloud adds capacity (mainly for architecture search), not features. |
| P7 | **Readable at any scale.** | Visualisation must stay usable for large graphs (semantic zoom, sampled value streaming). |
| P8 | **The current Python implementation is the reference.** | The new engine must reproduce its behaviour (conformance suite) unless a deliberate, recorded change of meaning is made. |

### 1.1 Formal model and semantics decisions

**Base model.**
- **Graph and values.** A graph `G = (V, E)` runs over discrete time steps
  `t0, t1, ...`. Each node `v` holds a value `val_t(v)`. An edge `(u, v)` makes
  `u` a predecessor of `v`; self-loops are allowed.
- **Node function.** A node computes its value with a function
  `F_v(Input_t(v), t) -> y`, where `Input_t(v)` holds the predecessors' values
  at `t`.
- **Batching.** Each node has an operand capacity `r`; larger input sets are
  split into batches. Batches are processed either across several ticks (the
  node is "mid-calculation") or forced into one tick, and either *exclusively*
  or *inclusively* (the running result is carried into the next batch).
- **Node kinds.** Nodes are *basic* or *complex*: *compressed* (an ordered
  chain) or *abstract* (a set of parallel nodes).
- **Processing schemes.** Concurrent (snapshot, then update all), forward
  (propagate from an active set) and manual (user-chosen sequence).
- **Simplification.** Nine topology types (by number of inputs and outputs),
  three split transformations (genesis/distribution/cross -> copies), and
  compression and abstraction, combined in an iterative simplification
  algorithm.

**Refinements the formal spec (Phase 0) must make** (decided 2026-11-17):

1. **Inputs are an ordered tuple, not a set.** A set loses order and merges
   equal values from different predecessors. Define `Pred(v)` as an ordered
   sequence (connection order) and `Input(v)` as a tuple.
2. **Keep `F(Input, t) -> y` as the baseline; nodes are *not* state machines.**
   `F` may be any deterministic procedure, not only a mathematical function.
   Batching and mid-calculation state belong to the **processor**, not the
   node. Memory follows a *visible memory* principle:
   - A node with memory keeps it **in its value** (the value domain is
     unrestricted) and reads it back through a **self-loop**, explicit or
     declared as implicit. Example: Buffer's value *is* the list. ContainerNode
     already works this way.
   - Time-driven nodes read `t` instead of keeping private counters
     (DataStream: `value = data[f(t)]`).
   - Randomness is **counter-based**: `rand(seed, node, t)`, with no shared
     global RNG.
   - The current code breaks this in places, and the spec must fix it:
     `BufferNode.buffer` is kept separately from its value, `DataStreamNode`
     keeps its own `iteration` counter, and `MutationNode` uses Python's global
     `random`. With multithreading, the global RNG makes results depend on
     thread order.
3. **Value domain.** A value can be anything: number, list, string, even a
   graph. Define the domain `D` as open, with a small set of built-in kinds.
4. **Input filtering.** The code drops inputs that fail `IsValidInput`, which
   changes how many inputs a node receives. Either specify this or remove it.
5. **Postponed nodes keep their previous value.** State this explicitly
   ("insufficient inputs -> postpone computation").
6. **Concurrent processing doesn't wait for inputs.** Unlike the classical
   computational-graph rule (an operation runs only once all its inputs are
   available), concurrent processing computes from the snapshot, so a path of
   k nodes takes k ticks. This belongs to the processing scheme, not the base
   definitions, and is intended. The resulting delayed weight updates make the
   concurrent MLP's equivalence with classic backprop behavioural, not exact.
7. **Define "semantically equivalent".** Proposed definition: two graphs are
   *trace-equivalent* if every externally observed node has the same value
   sequence. They are *delay-equivalent* if the sequences match after a fixed
   per-node shift.
   - The split transformations duplicate nodes. Copies of a **deterministic**
     node with the same inputs and the same initial value produce identical
     traces, so splitting is safe for them. It breaks only with hidden
     randomness or external edits to a single copy (GUI edits,
     `user_locked_value`). Visible memory and counter-based RNG (item 2) make
     every built-in node safe to split.
   - **Linked duplicates** (agreed): a split doesn't create independent copies.
     It shows *one* underlying node as several linked visual instances, so the
     processor computes it once. This removes the randomness and edit-divergence
     issues, and the extra compute.
   - **Decision**: complex nodes are a *view* (a lens over the flat graph).
     Execution always runs the flat graph's semantics, so switching granularity
     at runtime never changes results. Collapsing a chain into a one-tick
     operation is a separate, deliberate design operation ("Merge"), not part
     of simplification.
   - **Fixed 2026-11-17** in the Python reference: `CompressedNode` used to run
     its whole chain in one tick, and both complex node kinds re-read internal
     inputs during Phase 2 (order-dependent). They now gather all internal
     inputs in Phase 1 and only compute in Phase 2. Trace equivalence is
     covered by `reference/Tests/core/graph/test_complex_node_snapshot_semantics.py`.
8. **Simplification must terminate.** Probe results (2026-11-17):
   - If splitting is allowed on a graph with a single loop, the algorithm
     never ends. Example: `s->x, x->x, x->y`. Each split leaves `x` still a
     Cross node and adds a node.
   - The code avoids this by splitting only when the graph has **no cycles at
     all**. That is safe but stricter than needed.
   - On DAGs: dense layered graphs (up to 4x4x4x4) and 300 random DAGs all
     terminated, with at most one split.
   - Proof sketch for DAGs: splitting moves the multi-successor property
     strictly toward the sources in topological order, and sources end as
     entrypoints. Node count is bounded by the number of source-to-node paths.
     In theory that bound is exponential, but abstraction prevented growth in
     every test.
   - Rule to adopt: **never split a node that lies on a cycle**; document the
     termination measure in the spec.
9. **Universality can be proven, not only shown by examples.** Under
   concurrent processing, Container (an unbounded counter) + arithmetic + a
   step function (PiecewiseLinear) + self-loops can build a selector
   (`c*a + (1-c)*b`) and so simulate a Minsky counter machine. That would make
   the model Turing-complete (assuming unbounded precision). This answers "can
   it implement every algorithm" in theory. Manual and programmable scheduling
   remain the answer to "is it *easy* to express".

---

## 2. Target architecture

```
┌──────────────────────── Clients ────────────────────────┐
│ Desktop app (Tauri)   Web app (browser)   Python SDK     │
│      └──────── shared TypeScript UI ───────┘   (PyO3)    │
└──────────────┬──────────────────┬──────────────┬─────────┘
               │ in-process       │ WebSocket /  │ native
               │ or localhost     │ gRPC         │ binding
┌──────────────▼──────────────────▼──────────────▼─────────┐
│                    Zorvan Engine (Rust)                   │
│  Graph IR ─► Compiler passes ─► Execution plan ─► Runtime │
│  (spec)     validate, simplify,   flat arrays    schedulers│
│             balance delays, fuse, (SoA, CSR)     + workers │
│             partition                                      │
└──────────────┬──────────────────┬────────────────────────┘
          local CPU          browser (WASM)      cloud workers
```

### 2.1 Technology stack

| Layer | Choice | Rejected (why) |
|-------|--------|----------------|
| Engine | **Rust** (stable), `rayon` for parallelism | C++ (build pain, safety), Julia (embedding/WASM/distribution), Python+Numba (GIL, no browser), Mojo (immature) |
| Python SDK | **PyO3 + maturin** wheels (`pip install zorvan`) | Hand-written C API (too much maintenance) |
| Browser engine | **wasm-bindgen** build of the same crates | Separate JS engine (duplicate logic) |
| User node plugins | **Rust** (built-in), **Python** (prototyping), **WASM** (fast + sandboxed) | Native dynamic libraries (unsafe in cloud) |
| Graph format | Versioned **JSON** (readable) + **MessagePack** (large graphs) | Pickle-like formats (unsafe, not portable) |
| Engine API | **gRPC/Connect** for commands, **WebSocket** stream for live values (protocol defined in `proto/`) | REST only (poor for streaming) |
| UI | **TypeScript**, **PixiJS** (WebGL/WebGPU) canvas, **React or Svelte** for panels, **uPlot** / ECharts for plots | React Flow as main canvas (DOM-bound, slows down past a few thousand nodes); keeping PyQt (no web path) |
| Desktop shell | **Tauri** (engine runs in-process) | Electron (100+ MB, separate runtime) |
| Cloud | Containerised engine workers + job queue; Kubernetes only when needed | Building cloud first |

### 2.2 Engine internals (summary)

- **Values**: tagged enum: `F64`, `I64`, `Bool`, `List(Vec<Value>)` (needed for EA populations), later `Tensor`. Scalars are stored inline, not boxed.
- **State**: struct-of-arrays, **double-buffered** (read *t*, write *t+1*, swap). This *is* the snapshot semantics of concurrent processing, and it lets each tick run in parallel without locks.
- **Topology**: compiled into compressed adjacency (CSR) that keeps input order (P3).
- **Compiler passes**: validate → balance delays → fuse chains → vectorise same-type groups → partition for workers. Every pass must preserve traces (§1.1, item 7).
  Simplification structure guides the optimiser. A chain of pure nodes becomes a fused *pipeline* (one loop with k stage registers, so the k-tick latency is kept). A same-type group of pure nodes becomes a vectorised batch.
  Simplification as a *view* (semantic zoom) is a separate operation and never changes execution.
- **Delay edges**: delay is an edge property stored as a ring buffer in the engine. Nodes stay simple and graphs lose the explicit buffer nodes. The old `BufferNode` remains available for cases where the buffer *is* the model.
- **Schedulers** (one trait: "given state, which nodes run next?"):
  `Concurrent`, `Forward` (fire when inputs are ready, Petri-net style), `Manual` (explicit list), `Programmable` (sequence computed by another graph, a script or an agent).

### 2.3 Repository layout (monorepo, this repository)

```
/
├── Cargo.toml                 # Rust workspace
├── crates/
│   ├── zorvan-ir/             # graph spec types, serde, versioning, .cgjson importer
│   ├── zorvan-core/           # Value, Node trait, built-in node kinds
│   ├── zorvan-compiler/       # passes → execution plan
│   ├── zorvan-runtime/        # state store, schedulers, executor
│   ├── zorvan-server/         # engine API server binary
│   ├── zorvan-py/             # PyO3 bindings
│   └── zorvan-wasm/           # wasm-bindgen bindings
├── python/                    # Python SDK package (maturin project), examples
├── ui/                        # TypeScript UI (pnpm workspace)
├── desktop/                   # Tauri shell (src-tauri)
├── proto/                     # engine API schema
├── conformance/               # language-neutral cases: graph + inputs + expected trace
├── benchmarks/                # cross-implementation benchmark suite
├── reference/                 # current Python implementation, frozen as oracle
│   ├── zorvan_reference/      # (renamed from zorvan/)
│   ├── gui_framework/         # PyQt app, kept until UI parity (Phase 5)
│   └── Tests/                 # existing pytest suite
└── docs/
```

---

## 3. Phases

Sizing is relative: **S** (days), **M** (1–3 weeks), **L** (1–2 months), **XL** (more).
Each phase ends with explicit exit criteria. Don't start a phase until the
previous phase's exit criteria are met, except where noted as parallelisable.

### Phase 0 — Freeze and specify the reference · **M**

**Goal:** turn the current Python code into a precisely specified, testable oracle.

Tasks
1. Tag the current state: `v0.1.0-python`. The maintainer has designated `main` as the Python backup branch; do not create a separate `python-legacy` branch.
2. Fix only the rough edges that affect *correctness of the reference*:
   - Duplicate `Graph.AbstractNodes` definition (Graph.py ~L242 and ~L1168).
   - Delete `GraphProcessor_optimized_broken.py` and `adapters/__init___new.py`.
   - Re-enable or document the disabled Windows GUI tests (commit `ff02e307`).
3. Write `docs/spec/SEMANTICS.md`, the formal meaning of concurrent processing. Start from the base model in §1.1 and apply its refinements:
   - Tick = Phase 1 `UpdateInputs` over the snapshot, then Phase 2 `ProcessBatch`.
   - Input order = predecessor connection order; how `IsValidInput` filtering changes how many inputs a node gets.
   - Batch rules: `batchSize`, `inclusive`, `midCalculation` across ticks, `forcedBatchProcessing`.
   - `AbstractNode` flattening and `CompressedNode` chain order.
   - `user_locked_value`, `ResetValue`, `DataStreamNode` `initialDelay`/`streamDelay`, `BufferNode`/`SequencerNode` behaviour.
   - Self-loops and cycles.
   - Explicitly list *non-determinism* found (e.g. thread pools inside `AbstractNode`) and decide the intended behaviour.
4. Write `docs/spec/NODE_CATALOG.md`: every node kind, its inputs (ordered), its parameters, its state, its operation and its valid input types.
5. Write `docs/spec/IR.md`: the new graph format (model spec separated from view spec), versioning rules and the `.cgjson` → IR mapping.
6. Build the **conformance recorder**: a script that runs a graph on the Python reference and writes `conformance/<case>/{graph.json, inputs.json, trace.json}` (per-tick values of every node, with float tolerance rules).
   Seed cases: the `reference/Tests/core` scenarios, Fibonacci, the examples loader graphs, MLP (forward and training), ANFIS XOR, an EA run with a fixed seed, each node kind on its own.
7. Build `benchmarks/` and record the **baseline**. Reproduce the existing measurement: an XOR MLP for 5,000 epochs, concurrent Zorvan vs an equivalent NumPy MLP, which measured 3.91× slower. Add a **scaling** benchmark (hidden width 2 → 256, graph size 10² → 10⁵ nodes), because the XOR result alone doesn't show how the gap grows with size.
8. Restructure into the monorepo layout: move Python code to `reference/` and rename the package `zorvan` → `zorvan_reference` (mechanical rename, like the earlier `ComputationalGraphs` → `zorvan` one). Keep CI green.

Exit criteria
- [x] SEMANTICS.md, NODE_CATALOG.md and IR.md reviewed and accepted.
- [x] ≥ 1 conformance case per node kind, plus the end-to-end cases above, generated from the reference.
- [x] Baseline benchmark numbers recorded in `benchmarks/BASELINE.md`.
- [x] Reference test suite passes from its new location in CI.

### Phase 1 — Rust engine core (concurrent processing) · **L**

**Goal:** a Rust engine that reproduces the reference's concurrent processing and is much faster.

Tasks
1. Set up the Cargo workspace with `zorvan-ir`, `zorvan-core`, `zorvan-runtime`; CI on Windows, macOS and Linux (fmt, clippy, tests).
2. `zorvan-ir`: graph spec types, serde JSON + MessagePack, schema version, `.cgjson` importer.
3. `zorvan-core`: the `Value` enum, the `NodeKind` trait (operation, input validity, batch behaviour, state), and node registry.
4. Port node kinds in this priority order:
   1. Arithmetic: Addition, Subtraction, Multiplication, Division, Min, Max, Display, Container.
   2. Activations and derivatives: Sigmoid, Tanh, ReLU, Linear, Gaussian, PiecewiseLinear.
   3. Streams and memory: DataStream, DynamicDataStream, Buffer, Sequencer, MovingAverage, List, ExtractListElement, TrimList.
   4. Error: MeanSquared, MeanSquaredError.
   5. Fuzzy: GaussianMembership and its derivative nodes.
   6. EA: Population, TournamentSelection, BulkTournament, Crossover variants, Mutation, Elitism, BestFitnessTracker, DeJongSphere (with a seedable RNG).
   7. Composite: CompressedNode, AbstractNode (as structural containers for now).
5. `zorvan-runtime`: double-buffered state store, concurrent scheduler (single-threaded first, then `rayon`), pause/stop/step control, per-tick callbacks.
6. Conformance runner in Rust that replays every `conformance/` case.
7. Port graph-level operations: topology analysis (9 types), cycle detection, simplify/expand steps, subgraphs.
8. Benchmarks with `criterion`, compared against the baseline.

Exit criteria
- [ ] 100% of concurrent-mode conformance cases pass (or each difference is a recorded, deliberate change of meaning).
- [ ] Single-threaded: **≥ 10×** faster than the Python reference on the benchmark suite (initial target, revisit after the first measurements).
- [ ] Multi-threaded: ≥ 60% parallel efficiency on 8 cores for graphs ≥ 10k nodes (initial target).

### Phase 2 — Python SDK · **M** · *can overlap with late Phase 1*

**Goal:** scientists use the new engine from Python with no Rust knowledge.

Tasks
1. `zorvan-py` with PyO3; build wheels with maturin for Windows, macOS and Linux and CPython 3.10–3.13.
2. Pythonic API: graph building, connecting (ordered inputs), running, reading values and traces, saving and loading. Pick one naming convention (snake_case), with aliases for the old PascalCase names where cheap.
3. **Python custom nodes**: a node kind implemented as a Python class or function. Documented as the slow, convenient tier.
4. MLP / backprop / ANFIS graph *generators* ported as Python SDK helpers (they only build graphs, so Python is fine here).
5. Curated, neutral example set (purpose-built for teaching, as agreed): Fibonacci, a profit calculator, a basic MLP, a basic fuzzy system, a basic EA, one simple hybrid.
6. *Optional bridge:* point the existing PyQt GUI at the new engine through the SDK, so users get the speed before the new UI exists. Do this only if it's cheap.

Exit criteria
- [ ] `pip install zorvan` works on all three operating systems from CI-built wheels.
- [ ] All curated examples run on the Rust engine.
- [ ] SDK API reference documentation generated.

### Phase 3 — Compiler and performance · **L**

**Goal:** make the engine fast through compilation, keeping nodes as the unit of meaning (P1).

Tasks
1. `zorvan-compiler`: graph IR → execution plan (topology in CSR form, node state as struct-of-arrays, per-kind dispatch tables).
2. **Delay edges**: add to the IR, the runtime (ring buffers) and the `.cgjson` importer (map buffer-node patterns to delay edges where the meaning is identical).
3. **Delay-balancing pass**: compute path delays and insert delays automatically so parallel branches line up (retiming). This removes manual `initialDelay` arithmetic.
4. **Fusion pass**: chains of pure nodes → fused pipelines that keep per-tick latency (trace-preserving).
5. **Vectorisation pass**: same-type groups of pure nodes → SIMD batches.
   Node kinds declare whether they are `pure` (stateless, deterministic). Passes only touch pure nodes.
6. **Partitioning pass**: split large graphs into work chunks with good locality for `rayon`.
7. **Optional tensor-valued nodes** (P1: opt-in only), e.g. a dense layer node for users who want it.
8. Profiling tools: per-node and per-pass timing, exposed to clients later.

Exit criteria
- [ ] Delay balancing reproduces the hand-tuned MLP timing without explicit buffer nodes.
- [ ] Each pass can be switched off, and conformance results are identical with passes on and off.
- [ ] Benchmark report against "conventional methods" for the baseline workload, with an honest written analysis of where Zorvan wins and loses.

### Phase 4 — Engine API and sessions · **M**

**Goal:** any client can drive any engine, local or remote, through one protocol.

Tasks
1. `proto/`: commands (load graph, edit graph, compile, run, pause, step, stop, reset, set value, lock value) and queries (state, topology, traces).
2. **Subscriptions**: clients subscribe to nodes (visible or selected), and the engine streams sampled values (default 30–60 Hz) and per-tick events. It never streams everything by default.
3. Session model: a session = graph + engine state + scheduler, with several sessions per engine.
4. `zorvan-server`: a headless engine binary running in local mode (localhost, no authentication) and in server mode (authentication hooks only).
5. Clients: a Python client in the SDK and a small CLI (`zorvan run graph.json --ticks 1000`).
6. Versioning and compatibility rules for the protocol.

Exit criteria
- [ ] The Python SDK can drive a remote engine with the same API as the local one.
- [ ] Streaming holds steady with 100k-node graphs (only the subscribed set is sent).

### Phase 5 — New UI and desktop app · **XL**

**Goal:** a visual editor better than the PyQt one, on desktop first.

Tasks
1. `ui/` scaffold: TypeScript, Vite, React or Svelte (decide at the start of the phase), and an engine client generated from `proto/`.
2. **Canvas** on PixiJS: nodes, ordered input ports (with visible order numbers, which fixes today's "order isn't intuitive" problem), edges and delay-edge display, selection, multi-connect, copy/paste, grid and snapping, undo/redo.
3. **Semantic zoom** using the simplification hierarchy: zoomed out, compressed and abstract groups show as single blocks; zooming in expands them.
4. Live visualisation: colour by value, ANN colouring, inline sparklines, plot panels (uPlot).
5. Panels: node palette, inspector, execution controls, scheduler selection, examples, themes.
6. Layout algorithms (hierarchical, spring, MLP layouts), running in a web worker.
7. Custom node editor (Python and WASM node authoring).
8. `desktop/`: Tauri shell with the engine in-process, file associations, installers for Windows, macOS and Linux, auto-update.
9. Feature parity tracking against `docs/gui_rebuild/FEATURE_INVENTORY.md` (108 features): mark each feature as port, redesign or drop.

Exit criteria
- [ ] Every parity item marked "port" is done.
- [ ] Editing and running a 10k-node graph stays interactive (≥ 30 fps when panning or zooming).
- [ ] Desktop installers are published from CI. The PyQt app is marked deprecated (it stays in `reference/`).

### Phase 6 — Processing schedulers · **L** · *can start after Phase 1*

**Goal:** make the processing sequence first-class (P4).

Tasks
1. Write `docs/spec/SCHEDULERS.md`: the formal meaning of each scheduler and how it handles cycles, delays and termination.
2. **Forward scheduler**: fire nodes when their inputs are ready (token or Petri-net style), with stopping nodes, and a comparison against concurrent mode on the same graphs.
3. **Manual scheduler**: an explicit ordered list, editable in the UI (drag nodes into a sequence and step through it).
4. **Programmable scheduler**: the sequence is produced by (a) another Zorvan graph, (b) a Python script, or (c) an external agent through the API.
5. UI: show the sequence (highlight the active set, a timeline of firings).
6. Research note: which algorithm classes are easy or hard to express in each mode (feeds the "can it implement every algorithm" question).

Exit criteria
- [ ] All four schedulers pass their own conformance cases.
- [ ] The same example is shown in all four modes in the curated examples.

### Phase 7 — Web, WASM and cloud · **XL**

**Goal:** the same product in the browser, with optional cloud compute.

Tasks
1. `zorvan-wasm` build; the UI runs the engine in a web worker with no server.
2. Web hosting of the UI (static site) with local-only mode as the default.
3. Cloud engine workers (containers) + job API + storage for graphs and results.
4. "Run on cloud" switch in the UI: upload the graph, attach to the remote session, stream results back.
5. Security: only WASM plugin nodes run in the cloud by default; Python nodes only in isolated containers; quotas and limits.
6. Accounts, authentication, usage metering. Billing is a separate business decision (see open questions).

Exit criteria
- [ ] The same graph runs identically in the browser, on the desktop and in the cloud (conformance cases pass in WASM).
- [ ] The cloud path handles at least 100 concurrent jobs in a load test.

### Phase 8 — Architecture search platform · **XL**

**Goal:** the long-term research goal: search methods that generate hybrid architectures.

Tasks
1. Search API (Python SDK first): define a search space, a mutation and rewiring operator set, a fitness function and a budget.
2. **Unconstrained random rewiring** as a built-in operator (P3), plus optional typed-port constraints for constrained search.
3. **Batch evaluation**: the engine evaluates many candidate graphs in parallel (locally across cores, in the cloud across workers).
4. Motif-level search using the simplification hierarchy (search over compressed and abstract blocks, not only single nodes).
5. Experiment tracking: candidates, fitness and lineage, viewable in the UI.
6. Example searches on standard small problems.

Exit criteria
- [ ] A complete search run (define → search → inspect the best graph visually) works offline and in the cloud.

### Research track (runs alongside the phases)
- **Universality proof**: show that concurrent processing can simulate a counter machine (§1.1, item 9). Implement the construction as a conformance example.
- **Equivalence theory**: formalise trace and delay equivalence; prove which simplification operations preserve them, and for which node classes.
- **Simplification with loops**: compress and render loop structures without losing meaning. Includes the termination argument (§1.1, item 8).
- **Processing-sequence theory**: expressiveness vs ease of design across the concurrent, forward, manual and programmable schedulers (feeds Phase 6).

### Backlog (not scheduled yet)
- **General gradient-graph transform**: each node kind declares its local derivative as a subgraph, and a transform builds the backward graph for *any* forward graph (generalises the old MLP forward/backward generator). Deferred by decision; likely after Phase 3.
- **Optional typed ports** in the IR and UI (constraint layer only, P3).
- GPU execution (wgpu compute) for large homogeneous groups.
- Distributed execution of a single huge graph across machines.
- Collaborative editing on the web.

---

## 4. Cross-cutting work

- **Testing:** conformance suite (shared by all implementations), unit tests per crate, property-based tests for compiler passes (passes must not change meaning), UI end-to-end tests (Playwright), benchmarks in CI with regression alerts.
- **CI/CD:** Rust (fmt, clippy, test) on three operating systems; wheels (maturin); WASM build; UI build and tests; Tauri installers on tags. Lint gates are *blocking* in the new code (unlike today's advisory ones).
- **Documentation:** specs in `docs/spec/`, SDK reference, user guide, curated tutorials.
- **Versioning:** semantic versioning for the engine, the IR schema and the protocol separately; IR migrations for old files.
- **Rough-edges backlog** (from the 2026-11-17 review): fix stale "ComputationalGraphs" names, the placeholder URL in `setup.py`, broken README emoji and links to missing files during Phase 0; the rest disappears with the restructure.

## 5. Risks

| Risk | Mitigation |
|------|------------|
| Rewrite stalls and the project has two half-working systems | Reference stays usable throughout; strict phase exit criteria; ship desktop + SDK before starting web/cloud |
| Semantics drift between Python and Rust | Conformance suite is the contract; any difference must be recorded in the decision log |
| Rust learning curve | Engine design kept simple (no unsafe, no clever lifetimes in public APIs); LLM-assisted, but the lead must understand the core crates |
| Scalar-node graphs still lose to dense matrix libraries | Be honest in benchmarks; position Zorvan on sparse, irregular and hybrid models; offer opt-in tensor nodes |
| Scope (three products) | Desktop + SDK is the first complete product; web and cloud are later phases |
| Running user code in the cloud | WASM sandbox by default; Python only in isolated containers |

## 6. Open questions

1. React or Svelte for the UI panels? (decide at the start of Phase 5)
2. Licensing once the cloud exists: stay fully MIT, or open-core (engine + desktop open, cloud service commercial)?
3. Beyond the XOR-vs-NumPy baseline (3.91×), which larger benchmark defines success (framework, model, dataset)?
4. Should `BufferNode`-based graphs be auto-converted to delay edges on import, or kept as-is and converted on request?
5. Minimum supported Python version for the SDK.

## 7. Decision log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-11-17 | Engine in Rust; TypeScript + PixiJS UI; Tauri desktop; PyO3 SDK; WASM for web | Speed + parallelism + one engine for desktop/web/cloud |
| 2026-11-17 | Engine reached through an API with several clients; offline desktop first, cloud optional | Offline completeness and a business path through cloud compute for search |
| 2026-11-17 | Stay in this repository as a monorepo; Python code becomes `reference/` | Avoid duplicate repos; keep history; Python acts as oracle |
| 2026-11-17 | Inputs stay ordered and untyped by default; types optional | Keeps fully random rewiring possible for search |
| 2026-11-17 | Delay becomes an edge property, plus an automatic balancing pass | Nodes stay simple without buffer-node clutter |
| 2026-11-17 | Research-specific demo examples removed from the GUI; curated neutral examples instead | Avoid steering users |
| 2026-11-17 | General backprop transform deferred to the backlog | Not needed for the first engine milestones |
| 2026-11-17 | View simplification is kept separate from execution transformations; compiler passes must be trace-preserving and only touch pure nodes | CompressedNode changed latency; node splitting can duplicate hidden state |
| 2026-11-17 | The formal spec refines the base model: ordered inputs, open value domain, visible memory | Semantics review (§1.1) |
| 2026-11-17 | Nodes stay `F(Input, t) → y` and are not state machines; memory lives in the value plus a self-loop; batching state belongs to the processor | Author's conceptual preference; keeps the baseline simple |
| 2026-11-17 | Complex nodes are views over the flat graph; "Merge" (one-tick chain) is a separate deliberate operation | Granularity switches must never change results |
| 2026-11-17 | Never split nodes that lie on a cycle | A self-loop makes unrestricted splitting run forever |
| 2026-11-20 | Keep `main` as the Python backup while rearchitecture work proceeds on its own branch; no separate `python-legacy` branch | Maintainer direction |

## 8. Status

| Phase | Status |
|-------|--------|
| 0 Freeze and specify | Complete (specs accepted; restructure, cleanup, conformance seeds, and benchmarks done; CI green; baseline tag `v0.1.0-python` created locally) |
| 1 Rust engine core | Not started |
| 2 Python SDK | Not started |
| 3 Compiler and performance | Not started |
| 4 Engine API | Not started |
| 5 UI and desktop | Not started |
| 6 Schedulers | Not started |
| 7 Web, WASM, cloud | Not started |
| 8 Search platform | Not started |

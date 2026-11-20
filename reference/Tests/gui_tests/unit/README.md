# GUI Unit Test Organization

This directory now uses feature-based subdirectories to group GUI unit tests.

## Directories

- `activation/` - activation dialog adapters, views, and viewmodels.
- `backprop/` - backprop configuration and viewmodel logic.
- `canvas/` - canvas state, viewport, layout, and command tests.
- `custom_node/` - custom node persistence, dialogs, registration, and palette refresh.
- `examples/` - examples loader and repository tests.
- `execution/` - execution controller/view/viewmodel tests.
- `file_io/` - file I/O dialog and viewmodel tests.
- `graph/` - graph creation dialogs and graph-level flow tests.
- `inspector/` - inspector panel adapters, views, and viewmodels.
- `layout/` - layout algorithm, adapter, and view tests.
- `learning_rate/` - learning rate UI and viewmodel tests.
- `main_window/` - main window action tests.
- `mlp/` - MLP dialog and generator viewmodel tests.
- `node_editor/` - node editor dialogs and viewmodels.
- `node_factory/` - node factory and registry tests.
- `node_properties/` - node properties, predecessors, and replacement dialogs.
- `palette/` - palette adapters, views, and viewmodels.
- `plot/` - plot adapter, config view, and plot view tests.
- `registry/` - registry and widget plugin system tests.
- `runtime/` - runtime behavior and persistence during graph execution.
- `state/` - state models, event bus, and snapshot tests.
- `theme/` - theme and color preferences tests.
- `window/` - window manager, subgraph icons, and view import tests.

## Convention

- If a test uses a live widget or dialog, it should generally live in `unit/<feature>/` near the corresponding viewmodel or adapter.
- If a test exercises more than one major UI component, move it to `integration/`.
- Keep `conftest.py` as the shared Qt fixture source for both unit and integration tests.

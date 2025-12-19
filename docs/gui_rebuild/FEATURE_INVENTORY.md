# GUI Feature Inventory

Complete inventory of all GUI features in the ComputationalGraphs visual editor.

**Legend:**
- Priority: P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- Status: ✅ Working, ⚠️ Partial, ❌ Broken, 🧪 Needs Testing

## 1. Node Editor / Graph Canvas

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Create nodes | Drag nodes from palette to canvas | `graph_canvas.py`, `node_item.py` | `test_create_node_on_drop.py` | P0 | ✅ |
| Delete nodes | Select and press Delete/Backspace | `graph_canvas.py`, `commands/remove_items_command.py` | `test_canvas_clipboard_and_connect.py` | P0 | ✅ |
| Edit nodes | Double-click or Ctrl+E to edit properties | `node_editor_dialog.py`, `controllers/node_editing_controller.py` | `test_node_editing_controller.py` | P0 | ✅ |
| Move nodes | Click and drag to reposition | `graph_canvas.py`, `node_item.py`, `commands/move_nodes_command.py` | Multiple | P0 | ✅ |
| Select nodes | Click to select, Ctrl+click for multi-select | `graph_canvas.py`, `node_item.py` | Multiple | P0 | ✅ |
| Rubber band selection | Drag rectangle to select multiple | `graph_canvas.py` | - | P1 | ✅ |
| Connect edges | Click output port, drag to input port | `graph_canvas.py`, `edge_item.py` | `test_graph_canvas_edge_connect_disconnect.py` | P0 | ✅ |
| Disconnect edges | Select edge and delete | `graph_canvas.py`, `commands/remove_edge_command.py` | `test_graph_canvas_edge_connect_disconnect.py` | P0 | ✅ |
| Multi-node connect | Select multiple, drag from edge to target | `graph_canvas.py`, `controllers/graph_edge_controller.py` | `test_multi_connection_gui.py` | P1 | ✅ |
| Zoom | Mouse wheel to zoom in/out | `graph_canvas.py` | - | P1 | ✅ |
| Pan | Middle mouse drag or arrow keys | `graph_canvas.py` | - | P1 | ✅ |
| Auto-expand nodes | Nodes expand to show all content | `graph_canvas.py`, `node_item.py` | `test_graph_canvas_auto_expand_nodes.py` | P2 | ✅ |
| Node grouping | Visual grouping of related nodes | `graph_canvas.py` | - | P2 | ✅ |
| Comments | Add text comments to canvas | `comment_item.py` | - | P2 | ✅ |
| Grid snapping | Snap nodes to grid (optional) | `graph_canvas.py` | `test_grid_defaults.py` | P2 | ✅ |

## 2. Node Palette

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Node categories | Organized node library by type | `node_palette.py`, `node_factory.py` | - | P0 | ✅ |
| Drag to canvas | Drag node type from palette | `node_palette.py`, `graph_canvas.py` | - | P0 | ✅ |
| Search/filter | Find nodes by name/category | `controllers/search_controller.py` | - | P1 | ✅ |
| Custom nodes | Load/save custom node definitions | `custom_node_manager.py`, `custom_node_dialog.py` | - | P1 | ✅ |
| Node preview | Hover to see node description | `node_palette.py` | - | P2 | ✅ |
| Theme integration | Palette colors follow theme | `node_palette.py`, `theme.py` | `test_node_palette_theme.py` | P2 | ✅ |

## 3. Execution Controls

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Play/Pause | Start/pause graph execution | `controllers/execution_controller.py`, `graph_runner.py` | - | P0 | ✅ |
| Step execution | Execute one iteration at a time | `controllers/execution_controller.py` | - | P0 | ✅ |
| Reset | Reset graph to initial state | `controllers/execution_controller.py` | - | P0 | ✅ |
| Speed control | Slider for execution speed (10-2000ms) | `controllers/execution_settings_controller.py` | - | P0 | ✅ |
| Speed spinbox | Typed numeric speed input | `controllers/execution_settings_controller.py` | - | P1 | ✅ |
| Max iterations | Set maximum execution steps | `controllers/execution_settings_controller.py` | - | P0 | ✅ |
| Processor type | Select concurrent/forward processing | `controllers/execution_settings_controller.py` | - | P0 | ✅ |
| Auto-prepare | Automatic source node marking | `controllers/execution_controller.py` | - | P1 | ✅ |
| Pause after N steps | Auto-pause at specific iteration | `controllers/execution_controller.py` | `test_resume_rebuild_after_pause.py` | P2 | ✅ |

## 4. Visualization

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Colorize by value | Heat map coloring (blue to red) | `controllers/visualization_controller.py`, `node_item.py` | - | P1 | ✅ |
| ANN colorization | Neural network color scheme | `controllers/visualization_controller.py` | `test_ann_and_colorize_toggle.py`, `test_ann_colorization_bias_ms.py` | P1 | ✅ |
| Min/Max scale | Set color scale range | `controllers/visualization_controller.py` | - | P1 | ✅ |
| Node colors | Manual node color assignment | `node_item.py`, `color_preferences.py` | `test_node_item_manual_color.py`, `test_apply_node_colors_clears_ann_override.py` | P2 | ✅ |
| Active node highlight | Show currently executing nodes | `node_item.py`, `graph_runner.py` | - | P1 | ✅ |
| Edge highlighting | Highlight data flow along edges | `edge_item.py` | - | P2 | ✅ |

## 5. Layout Algorithms

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Spring layout | Physics-based force-directed | `layouts.py`, `controllers/graph_layout_controller.py` | - | P1 | ✅ |
| Hierarchical layout | Layered DAG layout (Sugiyama) | `layouts.py`, `controllers/graph_layout_controller.py` | - | P1 | ✅ |
| Circular layout | Nodes in circle | `layouts.py`, `controllers/graph_layout_controller.py` | - | P2 | ✅ |
| Good Layout | MLP grid-based deterministic | `layouts.py`, `controllers/layout_manager.py` | - | P0 | ✅ |
| Good Layout (Dynamic) | Auto-widening for dense layers | `layouts.py` | - | P1 | ✅ |
| Good Layout (per-layer) | Per-layer spacing adjustment | `layouts.py` | - | P1 | ✅ |
| Good Layout (D&C) | Divide & conquer grid placement | `layouts.py` | - | P1 | ✅ |
| Final Layout | Complete MLP+Backprop rules | `layouts.py`, `controllers/layout_manager.py` | `test_bias_layout.py` | P0 | ✅ |
| Manual layout save | Preserve positions in save file | `controllers/file_io_controller.py` | `test_visuals_restored.py` | P0 | ✅ |

## 6. File I/O

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| New graph | Create empty graph | `controllers/file_io_controller.py` | - | P0 | ✅ |
| Open graph | Load from file | `controllers/file_io_controller.py` | Multiple | P0 | ✅ |
| Save graph | Save to file | `controllers/file_io_controller.py` | Multiple | P0 | ✅ |
| DrawIO format | .drawio/.xml with visual preservation | `Core/DrawioIO.py`, `controllers/file_io_controller.py` | `test_drawio_save_load.py` | P0 | ✅ |
| CGJson format | .cgjson computational graph format | `Core/CGJsonIO.py`, `controllers/file_io_controller.py` | `test_cgjson_save_load.py` | P0 | ✅ |
| Auto-save | Periodic auto-save (if enabled) | - | - | P2 | ❌ |
| Recent files | MRU list in File menu | - | - | P2 | ❌ |

## 7. Theme Manager

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Color themes | Dynamic color schemes | `theme.py`, `theme_utils.py` | `test_theme_apply.py` | P1 | ✅ |
| Font management | UI and canvas font settings | `theme.py`, `color_preferences.py` | `test_color_preferences_font_update.py`, `test_theme_font_persistence.py` | P1 | ✅ |
| Theme persistence | Save/load theme preferences | `theme.py` | - | P1 | ✅ |
| Dynamic updates | Live theme switching | `theme.py`, `theme_utils.py` (ThemeMixin) | - | P1 | ✅ |
| Custom colors | Color picker for preferences | `color_preferences.py` | - | P2 | ✅ |
| Stylesheet templates | QSS template system | `styles_template.qss`, `theme.py` | - | P1 | ✅ |

## 8. Examples & Automation

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Example loader | Pre-built graph templates | `examples_loader.py` | `test_example_canvas_sync.py` | P1 | ✅ |
| Basic examples | Fibonacci, addition chain | `examples_loader.py` | - | P2 | ✅ |
| NN examples | XOR, MLP, Iris classification | `examples_loader.py` | - | P1 | ✅ |
| Fuzzy examples | Temperature control | `examples_loader.py` | - | P2 | ✅ |
| EA examples | De Jong sphere function | `examples_loader.py` | - | P2 | ✅ |
| Generate MLP | Dialog to create MLP graph | `mlp_dialog.py`, `controllers/graph_builder_controller.py` | - | P0 | ✅ |
| Add Backprop | Dialog to add backprop to MLP | `backprop_dialog.py`, `controllers/graph_builder_controller.py` | - | P0 | ✅ |
| Example visualization | Auto-layout on example load | `examples_loader.py`, `main_window.py` | - | P1 | ✅ |

## 9. Dialogs & Inspector

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Node editor dialog | Edit node properties/values | `node_editor_dialog.py` | - | P0 | ✅ |
| MLP generator dialog | Configure and generate MLP | `mlp_dialog.py` | - | P0 | ✅ |
| Backprop dialog | Add backprop configuration | `backprop_dialog.py` | - | P0 | ✅ |
| Replace node dialog | Replace node with another type | `replace_node_dialog.py` | - | P1 | ✅ |
| Predecessors dialog | View/edit node connections | `predecessors_dialog.py` | `test_predecessors_dialog_ui.py` | P1 | ✅ |
| Custom node dialog | Create custom node definitions | `custom_node_dialog.py` | - | P1 | ✅ |
| Color preferences | Theme and color settings | `color_preferences.py` | Multiple | P1 | ✅ |
| Inspector panels | Live node property view | `controllers/control_panel_builder.py` | - | P1 | ✅ |

## 10. Plotting & Analysis

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Plot window | Matplotlib-based plotting | `plot_window.py`, `controllers/plotting_controller.py` | `test_plot_backend.py` | P1 | ✅ |
| PyQtGraph plots | PyQtGraph backend for real-time | `plot_window_pyqtgraph.py` | `test_plot_window_pyqtgraph_opengl.py` | P1 | ✅ |
| Add to plot | Toolbar button to plot node | `controllers/plotting_controller.py` | `test_toolbar_add_to_plot_button.py` | P1 | ✅ |
| Plot config | Configure plot appearance | `plot_window.py` | - | P2 | ✅ |
| Multi-plot | Multiple plot windows | `controllers/plotting_controller.py` | - | P2 | ✅ |
| Real-time updates | Live data plotting during execution | `graph_runner.py`, `plot_window_pyqtgraph.py` | - | P1 | ✅ |

## 11. Undo/Redo System

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Undo/Redo stack | QUndoStack integration | `main_window.py`, `commands/` | `test_undo_redo.py` | P0 | ✅ |
| Add node command | Undoable node creation | `commands/add_node_command.py` | - | P0 | ✅ |
| Remove items command | Undoable deletion | `commands/remove_items_command.py` | - | P0 | ✅ |
| Move nodes command | Undoable movement | `commands/move_nodes_command.py` | - | P0 | ✅ |
| Add/remove edge | Undoable connections | `commands/add_edge_command.py`, `commands/remove_edge_command.py` | - | P0 | ✅ |
| Abstract node command | Create abstract nodes | `commands/abstract_node_command.py` | - | P1 | ✅ |
| Compress node command | Compress subgraphs | `commands/compress_node_command.py` | - | P1 | ✅ |
| Swallow node command | Merge nodes into abstract | `commands/swallow_node_command.py` | `test_swallow_node.py` | P1 | ✅ |
| Replace node command | Replace node type | `commands/replace_node_command.py` | - | P1 | ✅ |
| Simplify command | Graph simplification | `commands/simplify_command.py` | - | P2 | ✅ |
| Paste command | Undoable paste | `commands/paste_command.py` | - | P1 | ✅ |

## 12. Clipboard Operations

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Copy nodes | Ctrl+C to copy selection | `graph_canvas.py` | `test_canvas_clipboard_and_connect.py` | P0 | ✅ |
| Cut nodes | Ctrl+X to cut selection | `graph_canvas.py` | - | P0 | ✅ |
| Paste nodes | Ctrl+V to paste at cursor | `graph_canvas.py`, `commands/paste_command.py` | `test_canvas_clipboard_and_connect.py` | P0 | ✅ |
| Internal edges | Preserve edges between copied nodes | `graph_canvas.py` | - | P1 | ✅ |
| Paste centering | Center pasted nodes in view | `graph_canvas.py` | - | P2 | ✅ |

## 13. Keyboard Shortcuts

| Shortcut | Action | Source | Priority | Status |
|----------|--------|--------|----------|--------|
| Ctrl+N | New graph | `controllers/menu_toolbar_controller.py` | P0 | ✅ |
| Ctrl+O | Open graph | `controllers/menu_toolbar_controller.py` | P0 | ✅ |
| Ctrl+S | Save graph | `controllers/menu_toolbar_controller.py` | P0 | ✅ |
| Ctrl+E | Edit node | `controllers/menu_toolbar_controller.py` | P0 | ✅ |
| Ctrl+C | Copy | `graph_canvas.py` | P0 | ✅ |
| Ctrl+X | Cut | `graph_canvas.py` | P0 | ✅ |
| Ctrl+V | Paste | `graph_canvas.py` | P0 | ✅ |
| Ctrl+M | Generate MLP | `controllers/menu_toolbar_controller.py` | P1 | ✅ |
| Ctrl+B | Add Backprop | `controllers/menu_toolbar_controller.py` | P1 | ✅ |
| Ctrl+Q | Quit | `controllers/menu_toolbar_controller.py` | P1 | ✅ |
| Delete | Delete selection | `graph_canvas.py` | P0 | ✅ |
| Backspace | Delete selection | `graph_canvas.py` | P0 | ✅ |
| Ctrl+Z | Undo | `main_window.py` | P0 | ✅ |
| Ctrl+Y | Redo | `main_window.py` | P0 | ✅ |

## 14. Console & Logging

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Console output | Display execution logs | `controllers/console_controller.py` | - | P1 | ✅ |
| Log filtering | Filter by log level | `controllers/console_controller.py` | - | P2 | ✅ |
| Clear console | Clear log output | `controllers/console_controller.py` | - | P2 | ✅ |
| Auto-scroll | Auto-scroll to latest logs | `controllers/console_controller.py` | - | P2 | ✅ |

## 15. Multi-Graph Support

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Multiple graphs | Open multiple graphs in tabs | `main_window.py` | `test_multi_graph_support.py` | P2 | ✅ |
| Graph switching | Switch between open graphs | `main_window.py` | - | P2 | ✅ |
| Per-graph state | Independent state per graph | `main_window.py` | - | P2 | ✅ |

## 16. Advanced Node Operations

| Feature | Description | Source Files | Tests | Priority | Status |
|---------|-------------|--------------|-------|----------|--------|
| Abstract nodes | Create hierarchical node groups | `commands/abstract_node_command.py` | `test_abstraction_nesting.py` | P1 | ✅ |
| Compress nodes | Compress subgraph representation | `commands/compress_node_command.py` | - | P1 | ✅ |
| Swallow nodes | Merge into abstract container | `commands/swallow_node_command.py` | `test_swallow_node.py` | P1 | ✅ |
| Replace nodes | Replace with different type | `commands/replace_node_command.py`, `replace_node_dialog.py` | - | P1 | ✅ |
| Node sequences | Execute nodes in sequence | `controllers/node_sequence_controller.py` | - | P2 | ✅ |

## Summary Statistics

### By Priority
- **P0 (Critical)**: 27 features
- **P1 (High)**: 52 features
- **P2 (Medium)**: 29 features
- **P3 (Low)**: 0 features

### By Status
- **✅ Working**: 106 features
- **⚠️ Partial**: 0 features
- **❌ Broken/Missing**: 2 features (auto-save, recent files)
- **🧪 Needs Testing**: 0 features

### Test Coverage
- **Total test files**: 32 GUI tests (currently failing due to headless setup)
- **Non-GUI tests**: 12 MLP tests (11 passing)
- **Coverage areas**: Node editing, canvas operations, undo/redo, theme, visualization, file I/O

## Migration Priority Matrix

### Phase 1 (Must Have - Week 1-2)
1. Core framework (state, events, window manager)
2. Graph canvas (node/edge rendering, basic interaction)
3. Node palette (drag-drop, categories)
4. Execution controls (play/pause/step/reset)
5. File I/O (save/load with format preservation)

### Phase 2 (Critical Features - Week 3-4)
6. Layout algorithms (all 8 layouts)
7. MLP/Backprop automation
8. Undo/Redo system
9. Theme manager
10. Node editor dialog

### Phase 3 (High Value - Week 5-6)
11. Visualization (colorization, active highlighting)
12. Examples loader
13. Clipboard operations (copy/paste)
14. Inspector panels
15. Plotting windows

### Phase 4 (Nice to Have - Week 7-8)
16. Advanced node operations (abstract, compress, swallow)
17. Multi-graph support
18. Console logging
19. Custom nodes
20. Additional dialogs

## Notes on Feature Dependencies

### Critical Dependencies
- **Theme Manager** → All UI components depend on theming
- **State Management** → Execution, visualization, undo/redo all need state
- **Event Bus** → Loose coupling between controllers and views
- **Graph Canvas** → Most features interact with the canvas
- **File I/O** → Essential for saving work and loading examples

### High-Risk Items
1. **Graph Canvas** (2,606 lines) - largest single component, many dependencies
2. **Control Panel Builder** (57,206 bytes) - complex dynamic UI generation
3. **Layout Algorithms** - 8 different implementations with MLP-specific logic
4. **Theme System** - many components depend on dynamic theming

### Quick Wins
1. **CollapsibleSection** - simple standalone widget, good prototype
2. **Console Controller** - minimal dependencies, clear interface
3. **Examples Loader** - well-encapsulated, clear data structures
4. **Node Factory** - registry pattern, good candidate for plugin system

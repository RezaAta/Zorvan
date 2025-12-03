"""
Execution Controller - handles graph execution operations.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages play/pause/step/reset operations and execution state.
"""

from PyQt6.QtWidgets import QApplication, QMessageBox


class ExecutionController:
    """Controller for graph execution operations.

    Manages the execution lifecycle (play, pause, resume, step, reset)
    and coordinates between the main window UI and the GraphRunner.
    """

    def __init__(self, main_window):
        """Initialize the execution controller.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window

    @property
    def graph(self):
        """Access the current graph from main window."""
        return self.main_window.graph

    @property
    def graph_runner(self):
        """Access the graph runner from main window."""
        return self.main_window.graph_runner

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    def play(self):
        """Start graph execution."""
        # Avoid rebuilding if the canvas already contains the same nodes as the current graph.
        try:
            canvas_nodes = (
                set(self.canvas.node_items.keys())
                if hasattr(self.canvas, "node_items")
                and self.canvas.node_items is not None
                else set()
            )
            graph_nodes = (
                set(self.graph.nodes)
                if self.graph and hasattr(self.graph, "nodes")
                else set()
            )

            if not canvas_nodes:
                if not self.main_window.skip_visualization:
                    self.main_window.rebuild_graph()
            else:
                if canvas_nodes != graph_nodes:
                    self.main_window.rebuild_graph()
        except Exception:
            self.main_window.rebuild_graph()

        max_steps = self.main_window.max_steps_spin.value()

        # Check if skip visualization (batch mode) is enabled
        if self.main_window.skip_visualization:
            self.run_batch_mode(max_steps)
        else:
            # Normal mode with visualization
            self.graph_runner.start(max_steps)
            self._set_running_state()
            self.status_bar.showMessage("Executing graph...")

    def pause(self):
        """Pause graph execution."""
        self.graph_runner.pause()
        self._set_paused_state()
        self.status_bar.showMessage("Paused")

    def resume(self):
        """Resume execution - works both during pause and after completion.

        If canvas has been modified (nodes added/removed), rebuilds the graph first.
        If execution completed (current_step >= max_steps), extends the run by the
        configured number of additional iterations without resetting the counter.
        """
        # Check if canvas has been modified - rebuild if needed
        try:
            canvas_nodes = (
                set(self.canvas.node_items.keys())
                if hasattr(self.canvas, "node_items") and self.canvas.node_items
                else set()
            )
            graph_nodes = (
                set(self.graph.nodes)
                if self.graph and hasattr(self.graph, "nodes")
                else set()
            )
            if canvas_nodes != graph_nodes:
                self.main_window.rebuild_graph()
        except Exception:
            pass

        # Check if execution completed (not just paused)
        if self.graph_runner.current_step >= self.graph_runner.max_steps:
            # Execution finished - run additional iterations from current step
            additional_steps = self.main_window.max_steps_spin.value()
            new_total = self.graph_runner.current_step + additional_steps

            # Check if skip visualization (batch mode) is enabled
            if self.main_window.skip_visualization:
                self._run_batch_resume(additional_steps)
            else:
                # Use start_additional to run exactly additional_steps more iterations
                self.graph_runner.start_additional(additional_steps)
                self._set_running_state()
                self.status_bar.showMessage(
                    f"Resumed: running {additional_steps} more iterations (total: {new_total})"
                )
        else:
            # Normal resume from pause
            # If there was a rebuild, GraphRunner.set_graph() will have stopped any
            # existing background worker. In that case we need to start a fresh
            # worker that will use the new GraphProcessor instance. Otherwise, if
            # a worker thread still exists, simply resume it.
            try:
                if (
                    not hasattr(self.graph_runner, "_exec_thread")
                    or self.graph_runner._exec_thread is None
                    or not self.graph_runner._exec_thread.is_alive()
                ):
                    # If current_step < max_steps, start a new worker to continue
                    if self.graph_runner.current_step < self.graph_runner.max_steps:
                        # Use start with reset_step_counter=False to preserve current_step
                        self.graph_runner.start(
                            max_steps=self.graph_runner.max_steps,
                            reset_step_counter=False,
                        )
                else:
                    self.graph_runner.resume()
            except Exception:
                # Fall back to resume if anything unexpected happens
                try:
                    self.graph_runner.resume()
                except Exception:
                    pass
            self._set_running_state()
            self.status_bar.showMessage("Resumed execution")

    def _run_batch_resume(self, additional_steps):
        """Run additional steps in batch mode after completion."""
        from PyQt6.QtWidgets import QApplication

        self._set_batch_mode_state()
        start_step = self.graph_runner.current_step
        self.status_bar.showMessage(
            f"Batch mode: Running {additional_steps} more steps..."
        )
        QApplication.processEvents()

        try:
            processor = self.graph_runner.graph_processor
            processor_type = self.graph_runner.processor_type
            use_multithreading = self.graph_runner.use_multithreading

            if processor_type == "forward":
                starting_nodes = None
                if hasattr(self.graph, "starting_nodes") and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes
                processor.ForwardProcessing(
                    iterations=additional_steps, starting_nodes=starting_nodes
                )
            elif processor_type == "manual":
                processor.ManualProcessing(
                    iterations=additional_steps,
                    computation_sequence=getattr(
                        self.graph, "manual_processing_sequence", None
                    ),
                )
            else:
                if use_multithreading:
                    processor.ComputeGraph(additional_steps)
                else:
                    processor.ComputeGraphSingleThread(additional_steps)

            # Update step counter
            new_step = start_step + additional_steps
            self.graph_runner.current_step = new_step
            self.graph_runner.max_steps = new_step
            self.main_window.step_label.setText(f"Step: {new_step}")

            # Update visuals
            if self.main_window.colorize_enabled:
                self.main_window.auto_detect_range()
            else:
                self.canvas.update_node_visuals(False, 0, 1)

            # Update plot
            if (
                self.main_window.plot_window
                and self.main_window.plot_window.isVisible()
            ):
                self.main_window.plot_window.update_plot(new_step)

            self.status_bar.showMessage(
                f"Batch resume complete: {additional_steps} steps (total: {new_step})"
            )
        except Exception as e:
            QMessageBox.critical(self.main_window, "Batch Resume Error", str(e))
            self.status_bar.showMessage("Batch resume failed")
        finally:
            self._set_stopped_state()

    def step(self):
        """Execute a single step."""
        if not self.graph_runner.is_running:
            self.main_window.rebuild_graph()

        self.graph_runner.single_step()

    def reset(self):
        """Full reset: restore graph to snapshot state AND reset processor."""
        self.graph_runner.reset()
        self.main_window.step_label.setText("Step: 0")

        self._set_stopped_state()

        # Reset visuals
        if self.main_window.colorize_enabled:
            self.main_window.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)

        self.status_bar.showMessage("Reset complete")

    def restore_graph(self):
        """Restore graph to iteration 0 state without changing iteration counter.

        This reverts all node values, buffer contents, and DataStream states to
        the snapshot taken at iteration 0, but preserves the current step count
        and keeps resume enabled.
        """
        current_step = self.graph_runner.current_step
        current_max_steps = self.graph_runner.max_steps

        if self.graph_runner.restore_graph_snapshot():
            # Keep the iteration counter and max_steps unchanged
            self.graph_runner.current_step = current_step
            self.graph_runner.max_steps = current_max_steps

            # Update visuals
            if self.main_window.colorize_enabled:
                self.main_window.auto_detect_range()
            else:
                self.canvas.update_node_visuals(False, 0, 1)

            # Don't call _set_stopped_state() - preserve resume button state
            # Just ensure play is enabled and we're not running
            self.main_window.play_btn.setEnabled(True)
            self.main_window.pause_btn.setEnabled(False)
            # Keep resume enabled if there was progress
            self.main_window.resume_btn.setEnabled(current_step > 0)
            self.main_window.threading_combo.setEnabled(True)
            if hasattr(self.main_window, "rebuild_btn"):
                self.main_window.rebuild_btn.setEnabled(True)
            if hasattr(self.main_window, "rebuild_exec_btn"):
                self.main_window.rebuild_exec_btn.setEnabled(True)

            self.status_bar.showMessage(
                f"Graph restored to iteration 0 state (step counter: {current_step})"
            )
        else:
            QMessageBox.warning(
                self.main_window,
                "Restore Failed",
                "No snapshot available. The graph has not been run yet or snapshot was not saved.",
            )

    def reset_processor(self):
        """Reset only the processor and iteration counter, preserving node values.

        This resets the iteration counter to 0 and reinitializes the processor state
        but keeps all node values unchanged.
        """
        self.graph_runner.reset_processor()
        self.main_window.step_label.setText("Step: 0")

        self._set_stopped_state()

        # Update visuals to show current node values
        if self.main_window.colorize_enabled:
            self.main_window.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)

        self.status_bar.showMessage("Processor reset (node values preserved)")

    def run_batch_mode(self, max_steps):
        """Run all steps at once without updating visuals until complete."""
        self._set_batch_mode_state()
        self.status_bar.showMessage(f"Batch mode: Running {max_steps} steps...")

        # Force UI update to show status
        QApplication.processEvents()

        try:
            processor = self.graph_runner.graph_processor
            use_multithreading = self.graph_runner.use_multithreading
            processor_type = self.graph_runner.processor_type

            if processor_type == "forward":
                # Forward Processing
                starting_nodes = None
                if hasattr(self.graph, "starting_nodes") and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes
                processor.ForwardProcessing(
                    iterations=max_steps, starting_nodes=starting_nodes
                )
            elif processor_type == "manual":
                # Manual processing in batch
                processor.ManualProcessing(
                    iterations=max_steps,
                    computation_sequence=getattr(
                        self.graph, "manual_processing_sequence", None
                    ),
                )
            else:
                # Concurrent processing
                if use_multithreading:
                    processor.ComputeGraph(max_steps)
                else:
                    processor.ComputeGraphSingleThread(max_steps)

            # Update visuals once at the end
            self.main_window.step_label.setText(f"Step: {max_steps}")
            if self.main_window.colorize_enabled:
                self.main_window.auto_detect_range()
            else:
                self.canvas.update_node_visuals(False, 0, 1)

            # Update plot window if open
            if (
                self.main_window.plot_window
                and self.main_window.plot_window.isVisible()
            ):
                self.main_window.plot_window.update_plot(max_steps)

            self.status_bar.showMessage(
                f"Batch mode complete: {max_steps} steps executed"
            )

        except Exception as e:
            QMessageBox.critical(self.main_window, "Batch Execution Error", str(e))
            self.status_bar.showMessage("Batch execution failed")

        finally:
            self._set_stopped_state()

    def on_step_completed(self, step):
        """Handle step completion callback from GraphRunner."""
        self.main_window.step_label.setText(f"Step: {step}")

        # If 'Skip Graph Visualization' is enabled, skip canvas/visual updates
        if self.main_window.skip_visualization:
            # Update plot window if open (unless skip_plotting is enabled)
            if (
                not self.main_window.skip_plotting
                and self.main_window.plot_window
                and self.main_window.plot_window.isVisible()
            ):
                try:
                    self.main_window.plot_window.update_plot(step)
                except Exception:
                    pass
            return

        # Update node visuals
        if self.main_window.colorize_enabled:
            self.main_window.auto_detect_range()
        else:
            self.canvas.update_node_visuals(False, 0, 1)

        # Highlight active nodes for Forward Processing and Manual Processing
        if self.graph_runner.processor_type in ("forward", "manual"):
            self.canvas.highlight_active_nodes(self.graph_runner.active_nodes)
            # Optionally dim nodes that are marked as 'processed'
            if (
                self.main_window.dim_processed_check.isChecked()
                and self.graph_runner.processor_type == "forward"
            ):
                self._apply_processed_node_dimming()
        else:
            self.canvas.highlight_active_nodes([])

        # Update plot window if open
        if (
            not self.main_window.skip_plotting
            and self.main_window.plot_window
            and self.main_window.plot_window.isVisible()
        ):
            self.main_window.plot_window.update_plot(step)

    def on_execution_finished(self):
        """Handle execution completion callback."""
        self._set_stopped_state()
        self.status_bar.showMessage("Execution finished")

    def on_error(self, message):
        """Handle execution error callback."""
        QMessageBox.critical(self.main_window, "Execution Error", message)
        self._set_stopped_state()
        self.status_bar.showMessage("Error occurred")

    # UI State Management

    def _set_running_state(self):
        """Set UI to running state."""
        self.main_window.play_btn.setEnabled(False)
        self.main_window.pause_btn.setEnabled(True)
        self.main_window.resume_btn.setEnabled(False)
        self.main_window.threading_combo.setEnabled(False)
        if hasattr(self.main_window, "rebuild_btn"):
            self.main_window.rebuild_btn.setEnabled(False)
        if hasattr(self.main_window, "rebuild_exec_btn"):
            self.main_window.rebuild_exec_btn.setEnabled(False)

    def _set_paused_state(self):
        """Set UI to paused state."""
        self.main_window.play_btn.setEnabled(False)
        self.main_window.pause_btn.setEnabled(False)
        self.main_window.resume_btn.setEnabled(True)
        self.main_window.threading_combo.setEnabled(True)
        if hasattr(self.main_window, "rebuild_btn"):
            self.main_window.rebuild_btn.setEnabled(True)
        if hasattr(self.main_window, "rebuild_exec_btn"):
            self.main_window.rebuild_exec_btn.setEnabled(True)

    def _set_stopped_state(self):
        """Set UI to stopped state."""
        self.main_window.play_btn.setEnabled(True)
        self.main_window.pause_btn.setEnabled(False)
        # Enable resume if execution completed (allows continuing with more iterations)
        can_resume = (
            self.graph_runner.current_step > 0
            and self.graph_runner.current_step >= self.graph_runner.max_steps
        )
        self.main_window.resume_btn.setEnabled(can_resume)
        self.main_window.threading_combo.setEnabled(True)
        if hasattr(self.main_window, "rebuild_btn"):
            self.main_window.rebuild_btn.setEnabled(True)
        if hasattr(self.main_window, "rebuild_exec_btn"):
            self.main_window.rebuild_exec_btn.setEnabled(True)

    def _set_batch_mode_state(self):
        """Set UI to batch mode state."""
        self.main_window.play_btn.setEnabled(False)
        self.main_window.pause_btn.setEnabled(False)
        self.main_window.threading_combo.setEnabled(False)

    def _apply_processed_node_dimming(self):
        """Apply dimming to processed nodes in forward processing mode."""
        gp = getattr(self.graph_runner, "graph_processor", None)
        if gp and hasattr(gp, "_node_status"):
            processed_nodes = {
                n for n, s in gp._node_status.items() if s == "processed"
            }
            active_set = set(self.graph_runner.active_nodes)
            for node, node_item in self.canvas.node_items.items():
                if node in active_set:
                    node_item.setOpacity(1.0)
                elif node in processed_nodes:
                    node_item.setOpacity(0.25)
                else:
                    node_item.setOpacity(1.0)
                try:
                    node_item.update()
                except Exception:
                    pass
        else:
            for node_item in self.canvas.node_items.values():
                node_item.setOpacity(1.0)
                try:
                    node_item.update()
                except Exception:
                    pass

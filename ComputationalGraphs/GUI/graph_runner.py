"""
Graph execution runner with Qt integration.
"""

from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor


class GraphRunner(QObject):
    """Manages graph execution with timer-based stepping."""
    
    step_completed = pyqtSignal(int)  # Emits current step number
    execution_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.graph = None
        self.graph_processor = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        
        self.current_step = 0
        self.max_steps = 0
        self.is_running = False
        self.step_interval = 500  # milliseconds
        self.use_multithreading = False  # Default to single thread
        self.processor_type = "concurrent"  # "forward" or "concurrent" - default to concurrent
        self.active_nodes = []  # Track active nodes for forward processing highlighting
    
    def set_graph(self, graph):
        """Set the graph to execute."""
        self.graph = graph
        self.graph_processor = GraphProcessor(graph=self.graph, verbose=False)
        
        # If using forward processing, reset state to ensure fresh initialization
        if self.processor_type == "forward" and hasattr(self.graph_processor, 'reset_forward_state'):
            self.graph_processor.reset_forward_state()
        
        # If using forward processing, prepare the graph by marking source nodes as processed
        if self.processor_type == "forward":
            if hasattr(self.graph_processor, 'mark_source_nodes_as_processed'):
                self.graph_processor.mark_source_nodes_as_processed()
            # Do NOT automatically mark ContainerNodes as processed here.
            # Marking container (weight) nodes should be handled explicitly
            # by graph builders or user actions so they can participate in
            # forward-processing cycles and updates correctly.
    
    def start(self, max_steps=100):
        """Start continuous execution."""
        if not self.graph:
            self.error_occurred.emit("No graph loaded")
            return
        
        self.max_steps = max_steps
        self.current_step = 0
        self.is_running = True
        
        # Update adjacency matrix
        try:
            self.graph.UpdateAdjacencyMatrix()
        except Exception as e:
            self.error_occurred.emit(f"Graph update failed: {str(e)}")
            return
        
        self.timer.start(self.step_interval)
    
    def pause(self):
        """Pause execution."""
        self.is_running = False
        self.timer.stop()
    
    def resume(self):
        """Resume execution."""
        if not self.is_running and self.current_step < self.max_steps:
            self.is_running = True
            self.timer.start(self.step_interval)
    
    def step(self):
        """Execute one step of the graph."""
        if not self.graph or self.current_step >= self.max_steps:
            self.stop()
            return
        
        try:
            if self.processor_type == "forward":
                # Forward Processing execution
                # Execute one iteration
                # Explicitly pass starting_nodes to ensure correct initialization
                starting_nodes = None
                if hasattr(self.graph, 'starting_nodes') and self.graph.starting_nodes:
                    starting_nodes = self.graph.starting_nodes
                
                self.graph_processor.ForwardProcessing(iterations=1, starting_nodes=starting_nodes)
                
                # Track nodes that were just processed (for highlighting)
                if hasattr(self.graph_processor, '_currently_processing_nodes'):
                    self.active_nodes = list(self.graph_processor._currently_processing_nodes)
                else:
                    self.active_nodes = []
                
                # Note: We don't stop when active_remaining == 0 because the graph
                # may reactivate nodes in subsequent iterations (e.g., DataStreamNodes cycling)
            else:
                # Concurrent processing (traditional)
                self.active_nodes = []  # No active node tracking for concurrent
                if self.use_multithreading:
                    self.graph_processor.ComputeGraph(1)
                else:
                    self.graph_processor.ComputeGraphSingleThread(1)
            
            self.current_step += 1
            self.step_completed.emit(self.current_step)
            
            if self.current_step >= self.max_steps:
                self.stop()
        
        except Exception as e:
            self.error_occurred.emit(f"Execution error at step {self.current_step}: {str(e)}")
            self.stop()
    
    def stop(self):
        """Stop execution."""
        self.is_running = False
        self.timer.stop()
        self.execution_finished.emit()
    
    def reset(self):
        """Reset execution state."""
        self.stop()
        self.current_step = 0
        self.active_nodes = []
        
        # Reset all nodes
        if self.graph:
            for node in self.graph.nodes:
                if hasattr(node, 'ResetValue'):
                    node.ResetValue()
        
        # Reset forward processing state
        if self.processor_type == "forward" and self.graph_processor:
            if hasattr(self.graph_processor, 'reset_forward_state'):
                self.graph_processor.reset_forward_state()
            
            # Re-prepare the graph for forward processing after reset
            if hasattr(self.graph_processor, 'mark_source_nodes_as_processed'):
                self.graph_processor.mark_source_nodes_as_processed()
            # Do NOT re-mark ContainerNodes here for the same reason described above.
    
    def set_speed(self, interval_ms):
        """Set the step interval in milliseconds."""
        self.step_interval = max(10, interval_ms)
        if self.timer.isActive():
            self.timer.setInterval(self.step_interval)
    
    def set_threading_mode(self, use_multithreading):
        """Set whether to use multithreading for graph execution.
        
        Args:
            use_multithreading: True for multi-threaded, False for single-threaded
        """
        self.use_multithreading = use_multithreading
    
    def set_processor_type(self, processor_type):
        """Set the processor type for graph execution.
        
        Args:
            processor_type: "forward" for Forward Processing (autonomous execution), 
                          "concurrent" for traditional concurrent processing
        """
        self.processor_type = processor_type
        
        # Reset forward state when switching to Forward Processing
        if processor_type == "forward" and self.graph_processor:
            if hasattr(self.graph_processor, 'reset_forward_state'):
                self.graph_processor.reset_forward_state()
            
            # Prepare the graph for forward processing by marking source nodes as processed
            if hasattr(self.graph_processor, 'mark_source_nodes_as_processed'):
                self.graph_processor.mark_source_nodes_as_processed()
            # Do NOT automatically mark ContainerNodes as processed here.
            # Marking container (weight) nodes should be handled explicitly
            # by graph builders or user actions so they can participate in
            # forward-processing cycles and updates correctly.
    
    def single_step(self):
        """Execute a single step without timer."""
        if not self.is_running:
            self.step()

"""
Tests for PlotViewModel - Pure Python plot data management.

Tests plot data collection, node management, backend selection without PyQt.
"""

import pytest
from gui_framework.viewmodels.plot_viewmodel import PlotViewModel, PlotDataPoint


class TestPlotViewModelInitialization:
    """Test PlotViewModel initialization."""
    
    def test_default_initialization(self):
        """Test default initialization."""
        vm = PlotViewModel()
        
        assert vm.get_max_iterations() == 100
        assert vm.get_backend() == 'matplotlib'
        assert vm.get_plotted_nodes() == []
        assert vm.get_current_iteration() == 0
    
    def test_custom_initialization(self):
        """Test initialization with custom values."""
        vm = PlotViewModel(max_iterations=500, backend='pyqtgraph')
        
        assert vm.get_max_iterations() == 500
        assert vm.get_backend() == 'pyqtgraph'
    
    def test_invalid_backend_fallback(self):
        """Test invalid backend falls back to matplotlib."""
        vm = PlotViewModel(backend='invalid')
        
        assert vm.get_backend() == 'matplotlib'


class TestPlotViewModelConfiguration:
    """Test configuration methods."""
    
    def test_set_max_iterations(self):
        """Test setting max iterations."""
        vm = PlotViewModel()
        vm.set_max_iterations(1000)
        
        assert vm.get_max_iterations() == 1000
    
    def test_set_max_iterations_minimum(self):
        """Test max iterations minimum enforced."""
        vm = PlotViewModel()
        vm.set_max_iterations(5)
        
        assert vm.get_max_iterations() == 10  # Minimum
    
    def test_set_backend(self):
        """Test setting backend."""
        vm = PlotViewModel()
        
        # Track property change
        changes = []
        vm.observe_property("backend_changed", lambda old, new: changes.append((old, new)))
        
        vm.set_backend('pyqtgraph')
        
        assert vm.get_backend() == 'pyqtgraph'
        assert len(changes) == 1
    
    def test_set_backend_no_change(self):
        """Test setting same backend doesn't trigger notification."""
        vm = PlotViewModel(backend='matplotlib')
        
        changes = []
        vm.observe_property("backend_changed", lambda old, new: changes.append((old, new)))
        
        vm.set_backend('matplotlib')
        
        assert len(changes) == 0  # No change
    
    def test_set_invalid_backend(self):
        """Test setting invalid backend is ignored."""
        vm = PlotViewModel(backend='matplotlib')
        vm.set_backend('invalid')
        
        assert vm.get_backend() == 'matplotlib'  # Unchanged


class TestPlotViewModelNodeManagement:
    """Test node management methods."""
    
    def test_add_node(self):
        """Test adding a node to plot."""
        vm = PlotViewModel()
        
        # Track property change
        changes = []
        vm.observe_property("nodes_changed", lambda old, new: changes.append((old, new)))
        
        vm.add_node("node_A")
        
        assert "node_A" in vm.get_plotted_nodes()
        assert vm.get_node_color("node_A") is not None
        assert len(changes) == 1
    
    def test_add_duplicate_node(self):
        """Test adding duplicate node is ignored."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        changes = []
        vm.observe_property("nodes_changed", lambda old, new: changes.append((old, new)))
        
        vm.add_node("node_A")  # Duplicate
        
        assert vm.get_plotted_nodes().count("node_A") == 1
        assert len(changes) == 0  # No change
    
    def test_remove_node(self):
        """Test removing a node from plot."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_node("node_B")
        
        vm.remove_node("node_A")
        
        assert "node_A" not in vm.get_plotted_nodes()
        assert "node_B" in vm.get_plotted_nodes()
    
    def test_remove_nonexistent_node(self):
        """Test removing non-existent node is safe."""
        vm = PlotViewModel()
        vm.remove_node("nonexistent")  # Should not raise
        
        assert vm.get_plotted_nodes() == []
    
    def test_set_nodes(self):
        """Test setting node list replaces existing."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        vm.set_nodes(["node_B", "node_C", "node_D"])
        
        assert vm.get_plotted_nodes() == ["node_B", "node_C", "node_D"]
        assert "node_A" not in vm.get_plotted_nodes()
    
    def test_node_color_assignment(self):
        """Test nodes get assigned colors."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_node("node_B")
        
        color_a = vm.get_node_color("node_A")
        color_b = vm.get_node_color("node_B")
        
        assert color_a is not None
        assert color_b is not None
        assert color_a != color_b  # Different colors
    
    def test_get_node_color_nonexistent(self):
        """Test getting color for non-existent node returns None."""
        vm = PlotViewModel()
        
        assert vm.get_node_color("nonexistent") is None


class TestPlotViewModelDataManagement:
    """Test data collection and management."""
    
    def test_add_data_point(self):
        """Test adding a data point."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        # Track property change
        changes = []
        vm.observe_property("data_updated", lambda old, new: changes.append((old, new)))
        
        vm.add_data_point("node_A", 42.5, iteration=0)
        
        data = vm.get_plot_data("node_A")
        assert len(data) == 1
        assert data[0].iteration == 0
        assert data[0].value == 42.5
        assert len(changes) == 1
    
    def test_add_data_point_uses_current_iteration(self):
        """Test adding data point without iteration uses current."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.set_current_iteration(5)
        
        vm.add_data_point("node_A", 10.0)
        
        data = vm.get_plot_data("node_A")
        assert data[0].iteration == 5
    
    def test_add_data_point_for_unplotted_node(self):
        """Test adding data for unplotted node is ignored."""
        vm = PlotViewModel()
        
        vm.add_data_point("unplotted", 100.0)
        
        assert vm.get_plot_data("unplotted") == []
    
    def test_add_multiple_data_points(self):
        """Test adding multiple data points."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        vm.add_data_point("node_A", 1.0, iteration=0)
        vm.add_data_point("node_A", 2.0, iteration=1)
        vm.add_data_point("node_A", 3.0, iteration=2)
        
        data = vm.get_plot_data("node_A")
        assert len(data) == 3
        assert [d.value for d in data] == [1.0, 2.0, 3.0]
    
    def test_data_trimming_at_max_iterations(self):
        """Test data is trimmed when exceeding max iterations."""
        vm = PlotViewModel(max_iterations=10)
        vm.add_node("node_A")
        
        # Add 15 data points
        for i in range(15):
            vm.add_data_point("node_A", float(i), iteration=i)
        
        data = vm.get_plot_data("node_A")
        assert len(data) == 10  # Trimmed to max
        assert data[0].iteration == 5  # First 5 dropped
        assert data[-1].iteration == 14
    
    def test_add_data_points_batch(self):
        """Test adding multiple nodes' data at once."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_node("node_B")
        
        vm.add_data_points({
            "node_A": 10.0,
            "node_B": 20.0
        }, iteration=0)
        
        assert len(vm.get_plot_data("node_A")) == 1
        assert len(vm.get_plot_data("node_B")) == 1
        assert vm.get_plot_data("node_A")[0].value == 10.0
        assert vm.get_plot_data("node_B")[0].value == 20.0
    
    def test_get_all_plot_data(self):
        """Test getting all plot data."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_node("node_B")
        
        vm.add_data_point("node_A", 1.0, iteration=0)
        vm.add_data_point("node_B", 2.0, iteration=0)
        
        all_data = vm.get_all_plot_data()
        
        assert "node_A" in all_data
        assert "node_B" in all_data
        assert len(all_data["node_A"]) == 1
        assert len(all_data["node_B"]) == 1
    
    def test_clear_data(self):
        """Test clearing all plot data."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_data_point("node_A", 1.0, iteration=0)
        vm.set_current_iteration(5)
        
        vm.clear_data()
        
        assert len(vm.get_plot_data("node_A")) == 0
        assert vm.get_current_iteration() == 0


class TestPlotViewModelStatistics:
    """Test statistical methods."""
    
    def test_get_data_point_count(self):
        """Test getting data point count."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        vm.add_data_point("node_A", 1.0, iteration=0)
        vm.add_data_point("node_A", 2.0, iteration=1)
        
        assert vm.get_data_point_count("node_A") == 2
    
    def test_get_data_point_count_nonexistent(self):
        """Test getting count for non-existent node."""
        vm = PlotViewModel()
        
        assert vm.get_data_point_count("nonexistent") == 0
    
    def test_get_value_range(self):
        """Test getting min/max value range."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        vm.add_data_point("node_A", 5.0, iteration=0)
        vm.add_data_point("node_A", 10.0, iteration=1)
        vm.add_data_point("node_A", 2.0, iteration=2)
        
        min_val, max_val = vm.get_value_range("node_A")
        
        assert min_val == 2.0
        assert max_val == 10.0
    
    def test_get_value_range_no_data(self):
        """Test getting range with no data returns None."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        assert vm.get_value_range("node_A") is None
    
    def test_get_iteration_range(self):
        """Test getting iteration range across all data."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        vm.add_node("node_B")
        
        vm.add_data_point("node_A", 1.0, iteration=0)
        vm.add_data_point("node_A", 2.0, iteration=5)
        vm.add_data_point("node_B", 3.0, iteration=10)
        
        min_iter, max_iter = vm.get_iteration_range()
        
        assert min_iter == 0
        assert max_iter == 10
    
    def test_get_iteration_range_no_data(self):
        """Test getting iteration range with no data."""
        vm = PlotViewModel()
        
        min_iter, max_iter = vm.get_iteration_range()
        
        assert min_iter == 0
        assert max_iter == 0


class TestPlotViewModelObservableProperties:
    """Test observable property notifications."""
    
    def test_data_updated_observable(self):
        """Test data_updated property triggers observers."""
        vm = PlotViewModel()
        vm.add_node("node_A")
        
        observed_values = []
        vm.observe_property("data_updated", lambda old, new: observed_values.append(new))
        
        vm.add_data_point("node_A", 1.0)
        vm.add_data_point("node_A", 2.0)
        
        assert len(observed_values) == 2
    
    def test_nodes_changed_observable(self):
        """Test nodes_changed property triggers observers."""
        vm = PlotViewModel()
        
        observed_values = []
        vm.observe_property("nodes_changed", lambda old, new: observed_values.append(new))
        
        vm.add_node("node_A")
        vm.add_node("node_B")
        vm.remove_node("node_A")
        
        assert len(observed_values) == 3
    
    def test_backend_changed_observable(self):
        """Test backend_changed property triggers observers."""
        vm = PlotViewModel()
        
        observed_values = []
        vm.observe_property("backend_changed", lambda old, new: observed_values.append(new))
        
        vm.set_backend('pyqtgraph')
        
        assert len(observed_values) == 1

"""
Test MovingAverageNode functionality in both continuous and batch modes.
"""

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.DataStreamNode import DataStreamNode
from ComputationalGraphs.Nodes.MovingAverageNode import MovingAverageNode

def test_moving_average_continuous():
    """Test continuous mode - should update average every iteration."""
    print("=" * 60)
    print("TEST 1: MovingAverageNode - Continuous Mode")
    print("=" * 60)
    
    # Create graph
    graph = Graph()
    
    # Create data stream with values [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    data_stream = DataStreamNode(name="DataStream", data=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    
    # Create moving average node with buffer size 3, continuous mode
    moving_avg = MovingAverageNode(name="MovingAvg", size=3, mode='continuous', allowNone=False)
    moving_avg.AddPreNode(data_stream)
    
    # Add nodes to graph
    graph.AddNode(data_stream, moving_avg)
    graph.starting_nodes = [data_stream]
    graph.UpdateAdjacencyMatrix()
    
    # Process graph
    processor = GraphProcessor(graph)
    
    print("\nExpected behavior:")
    print("Iteration 1: buffer=[1], avg=1.0")
    print("Iteration 2: buffer=[1,2], avg=1.5")
    print("Iteration 3: buffer=[1,2,3], avg=2.0")
    print("Iteration 4: buffer=[2,3,4], avg=3.0")
    print("Iteration 5: buffer=[3,4,5], avg=4.0")
    print("...\n")
    
    print("Actual execution:")
    for i in range(10):
        processor.ComputeGraph(iterations=1)
        print(f"Iteration {i+1}: DataStream={data_stream.value}, MovingAvg={moving_avg.value:.2f}, Buffer={moving_avg.buffer}")
    
    # Verify final values
    expected_final_avg = (8 + 9 + 10) / 3  # Last 3 values
    actual_final_avg = moving_avg.value
    
    print(f"\nFinal average: {actual_final_avg:.2f} (expected: {expected_final_avg:.2f})")
    print(f"Test {'PASSED' if abs(actual_final_avg - expected_final_avg) < 0.01 else 'FAILED'}")
    print()

def test_moving_average_batch():
    """Test batch mode - should update average only when buffer fully replaced."""
    print("=" * 60)
    print("TEST 2: MovingAverageNode - Batch Mode")
    print("=" * 60)
    
    # Create graph
    graph = Graph()
    
    # Create data stream with values [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    data_stream = DataStreamNode(name="DataStream", data=[10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    
    # Create moving average node with buffer size 3, batch mode
    moving_avg = MovingAverageNode(name="MovingAvg", size=3, mode='batch', allowNone=False)
    moving_avg.AddPreNode(data_stream)
    
    # Add nodes to graph
    graph.AddNode(data_stream, moving_avg)
    graph.starting_nodes = [data_stream]
    graph.UpdateAdjacencyMatrix()
    
    # Process graph
    processor = GraphProcessor(graph)
    
    print("\nExpected behavior:")
    print("Iterations 1-3: Fill buffer, calculate first avg=(10+20+30)/3=20.0")
    print("Iterations 4-6: Replace buffer, calculate second avg=(40+50+60)/3=50.0")
    print("Iterations 7-9: Replace buffer, calculate third avg=(70+80+90)/3=80.0")
    print("Iteration 10: Partial replacement, avg stays at 80.0\n")
    
    print("Actual execution:")
    for i in range(10):
        processor.ComputeGraph(iterations=1)
        print(f"Iteration {i+1}: DataStream={data_stream.value}, MovingAvg={moving_avg.value:.2f}, Buffer={moving_avg.buffer}, Replacements={moving_avg.values_since_last_update}")
    
    # Verify final values
    expected_final_avg = 80.0  # (70+80+90)/3
    actual_final_avg = moving_avg.value
    
    print(f"\nFinal average: {actual_final_avg:.2f} (expected: {expected_final_avg:.2f})")
    print(f"Test {'PASSED' if abs(actual_final_avg - expected_final_avg) < 0.01 else 'FAILED'}")
    print()

def test_moving_average_reactivation():
    """Test if MovingAverageNode gets reactivated properly each iteration."""
    print("=" * 60)
    print("TEST 3: MovingAverageNode - Reactivation Test")
    print("=" * 60)
    
    # Create graph
    graph = Graph()
    
    # Create data stream
    data_stream = DataStreamNode(name="DataStream", data=[1, 2, 3, 4, 5])
    
    # Create moving average node
    moving_avg = MovingAverageNode(name="MovingAvg", size=2, mode='continuous', allowNone=False)
    moving_avg.AddPreNode(data_stream)
    
    # Add nodes to graph
    graph.AddNode(data_stream, moving_avg)
    graph.starting_nodes = [data_stream]
    graph.UpdateAdjacencyMatrix()
    
    # Process graph with verbose output
    processor = GraphProcessor(graph, verbose=True)
    
    print("\nRunning 5 iterations with verbose output:")
    print("This will show if MovingAvg gets activated each iteration\n")
    
    processor.ComputeGraph(iterations=5)
    
    print(f"\nFinal state:")
    print(f"  DataStream value: {data_stream.value}")
    print(f"  MovingAvg value: {moving_avg.value:.2f}")
    print(f"  MovingAvg buffer: {moving_avg.buffer}")
    print()

if __name__ == "__main__":
    test_moving_average_continuous()
    test_moving_average_batch()
    test_moving_average_reactivation()
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)

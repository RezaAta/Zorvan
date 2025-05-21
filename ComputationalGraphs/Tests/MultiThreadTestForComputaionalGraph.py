from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
import time

graph = Graph()
numberOfNodes = 16

for i in range(numberOfNodes):
    graph.AddNode(AdditionNode(name=f"node{i}",value=0))
    
graph.nodes[0].value = 1

for i in range(numberOfNodes):

    graph.ConnectPreNode(graph.nodes[i], graph.nodes[i-1], graph.nodes[i-2])



processor = GraphProcessor(graph, max_workers=1, verbose=False)
start_time = time.time()
processor.ComputeGraph(iterations = 10)
end_time = time.time()
singleThreadTime =  end_time - start_time
print(singleThreadTime)

processor = GraphProcessor(graph, max_workers=16, verbose=False)
start_time = time.time()
processor.ComputeGraph(iterations = 10)
end_time = time.time()
multiThreadTime =  end_time - start_time
print(multiThreadTime)

speedup = singleThreadTime/multiThreadTime
print(f"speedup rate is x{speedup}")

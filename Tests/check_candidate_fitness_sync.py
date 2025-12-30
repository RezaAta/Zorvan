import random

from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DeJongSphereNode import DeJongSphereNode
from ComputationalGraphs.Nodes.PopulationNode import PopulationNode


def sphere_function(x):
    return sum(i * i for i in x)


POP_SIZE = 10
GENOME_LENGTH = 5

# Create deterministic initial population
_r = random.Random(12345)
initial_population = [
    [_r.uniform(-5.12, 5.12) for _ in range(GENOME_LENGTH)] for _ in range(POP_SIZE)
]

# Build minimal graph
graph = Graph()
populationNode = PopulationNode(
    name="Population",
    data=initial_population,
    size=POP_SIZE,
    genome_length=GENOME_LENGTH,
    auto_generate=False,
)
populationBuffer = BufferNode("Pop_Buffer", size=1)
populationBuffer.AddPreNode(populationNode)
fitnessNode = DeJongSphereNode("Fitness")
fitnessNode.AddPreNode(populationNode)

graph.AddNode(populationNode, populationBuffer, fitnessNode)

# Run processor step-by-step and capture values
processor = GraphProcessor(graph=graph)
iter_count = POP_SIZE + 5  # run enough iterations to stream population
log = []
for it in range(iter_count):
    processor.ComputeGraph(1)
    pb = populationBuffer.value
    fn = fitnessNode.value
    pn = populationNode.value
    log.append((it + 1, pn, pb, fn))

# Analyze alignment
mismatches = []
for it, pn, pb, fn in log:
    if pb is not None and fn is not None:
        # expected fitness derived from pb
        expected = sphere_function(pb)
        if abs(expected - fn) > 1e-12:
            mismatches.append((it, pb, fn, expected))

print("Iterations logged:", len(log))
print("Found mismatches:", len(mismatches))
if mismatches:
    for m in mismatches[:10]:
        print("Iteration", m[0], "pb", m[1], "fn", m[2], "expected", m[3])
else:
    print(
        "No mismatches: populationBuffer value and fitnessNode value are aligned where both exist"
    )

# Also print a small sample of the log
print("\nSample log (iter, populationNode, populationBuffer, fitnessNode):")
for entry in log[:15]:
    print(entry)

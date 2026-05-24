import random

from zorvan.Nodes.CrossoverNode import CrossoverNode
from zorvan.Nodes.MutationNode import MutaionNode


def test_crossover_node_performs_point_crossover_with_seeded_randomness():
    random.seed(0)
    crossover = CrossoverNode(name="Crossover", rate=1.0, delay=0)

    child1, child2 = crossover.Operation([1, 2, 3], [4, 5, 6])

    assert child1 == [1, 2, 6]
    assert child2 == [4, 5, 3]


def test_mutation_node_with_zero_scale_preserves_input_when_rate_is_one():
    random.seed(0)
    mutation = MutaionNode(name="Mutation", rate=1.0, scale=0.0)

    assert mutation.Operation([1.0, 2.0]) == [1.0, 2.0]

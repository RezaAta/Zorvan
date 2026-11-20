"""Create one reference conformance case per built-in node kind."""

import json
import random
import tempfile
from pathlib import Path

from zorvan_reference.Core.CGJsonIO import save
from zorvan_reference.Core.Graph import Graph
from zorvan_reference.Nodes import (
    AbstractNode,
    AdditionNode,
    BestFitnessTrackerNode,
    BufferNode,
    BulkTournamentNode,
    CompressedNode,
    ContainerNode,
    CrossoverNode,
    DataStreamNode,
    DeJongSphereNode,
    DisplayNode,
    DivisionNode,
    DynamicDataStreamNode,
    ElitismNode,
    ExtractListElement,
    GaussianCenterDerivativeNode,
    GaussianMembershipNode,
    GaussianNode,
    GaussianSigmaDerivativeNode,
    InitializableContainerNode,
    LinearNode,
    LinearNodeDerivative,
    ListNode,
    MaxNode,
    MeanSquaredErrorNode,
    MeanSquaredNode,
    MinNode,
    MovingAverageNode,
    MultiplicationNode,
    MutaionNode,
    PiecewiseLinearNode,
    PopulationNode,
    ReLUDerivativeNode,
    ReLUNode,
    SequencerNode,
    SigmoidDerivativeNode,
    SigmoidNode,
    SingleCrossoverNode,
    SingleInputCrossover,
    SubtractionNode,
    TanhDerivativeNode,
    TanhNode,
    TournamentSelectionNode,
)

try:
    from .record_conformance import record_case
except ImportError:
    from record_conformance import record_case


NODE_TYPES = [
    AbstractNode,
    AdditionNode,
    BestFitnessTrackerNode,
    BufferNode,
    BulkTournamentNode,
    CompressedNode,
    ContainerNode,
    CrossoverNode,
    DataStreamNode,
    DeJongSphereNode,
    DisplayNode,
    DivisionNode,
    DynamicDataStreamNode,
    ElitismNode,
    ExtractListElement,
    GaussianCenterDerivativeNode,
    GaussianMembershipNode,
    GaussianNode,
    GaussianSigmaDerivativeNode,
    InitializableContainerNode,
    LinearNode,
    LinearNodeDerivative,
    ListNode,
    MaxNode,
    MeanSquaredErrorNode,
    MeanSquaredNode,
    MinNode,
    MovingAverageNode,
    MultiplicationNode,
    MutaionNode,
    PiecewiseLinearNode,
    PopulationNode,
    ReLUDerivativeNode,
    ReLUNode,
    SequencerNode,
    SigmoidDerivativeNode,
    SigmoidNode,
    SingleCrossoverNode,
    SingleInputCrossover,
    SubtractionNode,
    TanhDerivativeNode,
    TanhNode,
    TournamentSelectionNode,
]


def _sources_for(node_type, count):
    if node_type in {
        BestFitnessTrackerNode,
        BulkTournamentNode,
        ElitismNode,
        TournamentSelectionNode,
    }:
        values = [[1.0, 2.0], 0.25]
    elif node_type in {
        CrossoverNode,
        SingleInputCrossover,
        MutaionNode,
        PopulationNode,
        DeJongSphereNode,
    }:
        values = [[1.0, 2.0]]
    elif node_type is SingleCrossoverNode:
        values = [[1.0, 2.0, 3.0]]
    elif node_type is ExtractListElement:
        values = [[4.0, 5.0]]
    else:
        values = [2.0]
    return [values[index % len(values)] for index in range(count)]


def _build_structural_case(node_type, graph):
    if node_type is AbstractNode:
        source = ListNode("source")
        source.value = 2.0
        members = [LinearNode("member_a"), LinearNode("member_b")]
        for member in members:
            member.AddPreNode(source)
        target = AbstractNode("abstract", members)
        graph.AddNode(source, target)
        target.AddPreNode(source)
    elif node_type is CompressedNode:
        source = ListNode("source")
        source.value = 2.0
        first = LinearNode("first")
        last = SigmoidNode("last")
        first.AddPreNode(source)
        last.AddPreNode(first)
        first.id = "internal_first"
        last.id = "internal_last"
        target = CompressedNode("compressed", [first, last])
        graph.AddNode(source, target)
        target.AddPreNode(source)
        return

    source = ListNode("source")
    source.value = 2.0
    first = LinearNode("first")
    last = SigmoidNode("last")
    first.AddPreNode(source)
    last.AddPreNode(first)
    first.id = "internal_first"
    last.id = "internal_last"
    target = CompressedNode("compressed", [first, last])
    graph.AddNode(source, target)
    target.AddPreNode(source)


def _node_parameters(node_type):
    params = {"name": node_type.__name__}
    if node_type is DataStreamNode:
        params.update(data=[1.0, 2.0])
    if node_type in {CrossoverNode, SingleInputCrossover}:
        params.update(rate=1.0, delay=0)
    if node_type is TournamentSelectionNode:
        params.update(tournamentSize=1)
    if node_type is BulkTournamentNode:
        params.update(tournamentSize=1, populationSize=1, num_selections=1)
    if node_type is BestFitnessTrackerNode:
        params.update(population_size=1)
    if node_type is ElitismNode:
        params.update(population_size=1, num_elites=1)
    if node_type is PopulationNode:
        params.update(data=[[1.0, 2.0]], auto_generate=False)
    if node_type is ExtractListElement:
        params.update(index=0)
    return params


def _build_regular_case(node_type, graph):
    import inspect

    target = node_type(**_node_parameters(node_type))
    if node_type is SingleCrossoverNode:
        target.crossoverRate = 1.0
        target.delay = 0
    graph.AddNode(target)
    operation = inspect.signature(node_type.Operation)
    count = len(
        [
            parameter
            for name, parameter in operation.parameters.items()
            if name != "self"
            and parameter.kind not in {parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD}
        ]
    )
    for index, value in enumerate(_sources_for(node_type, count)):
        source = ListNode(f"source_{index}")
        source.value = value
        graph.AddNode(source)
        target.AddPreNode(source)


def _build_case(node_type):
    random.seed(1729)
    graph = Graph(name=node_type.__name__)
    if node_type in {AbstractNode, CompressedNode}:
        _build_structural_case(node_type, graph)
    else:
        _build_regular_case(node_type, graph)

    graph.UpdateAdjacencyMatrix()
    ticks = 2 if node_type is SingleInputCrossover else 1
    return graph, {"ticks": ticks, "max_workers": 1, "random_seed": 1729}


def generate(output_root):
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    errors = []
    for node_type in NODE_TYPES:
        case_name = node_type.__name__
        graph, inputs = _build_case(node_type)
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            graph_file = temp_dir / "graph.cgjson"
            inputs_file = temp_dir / "inputs.json"
            save(graph, str(graph_file))
            inputs_file.write_text(json.dumps(inputs), encoding="utf-8")
            try:
                record_case(graph_file, inputs_file, output_root / "nodes" / case_name)
            except Exception as error:  # keep generating to report every failure
                errors.append(f"{case_name}: {type(error).__name__}: {error}")
    if errors:
        raise RuntimeError("Failed conformance cases:\n" + "\n".join(errors))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="conformance")
    generate(parser.parse_args().output)

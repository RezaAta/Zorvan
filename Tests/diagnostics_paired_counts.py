from Experiments.exp_compare_ea_classic_vs_graph import run_comparison_trials

# Run a small paired experiment and collect debug counters from node modules
classic_results, graph_results = run_comparison_trials(
    num_trials=3, pop_size=21, generations=10, num_elites=1, genome_length=5
)

from ComputationalGraphs.Nodes.BulkTournamentNode import TOURNAMENTS_RUN

# Import counters
from ComputationalGraphs.Nodes.SingleInputCrossover import CHILDREN_PRODUCED

print("\nDiagnostics:")
print(f"BulkTournamentNode TOURNAMENTS_RUN = {TOURNAMENTS_RUN}")
print(f"SingleInputCrossover CHILDREN_PRODUCED = {CHILDREN_PRODUCED}")

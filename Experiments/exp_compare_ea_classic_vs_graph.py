# Moved from ComputationalGraphs/Tests/EATests/CompareClassicVsGraph_EA.py
# Renamed to Experiments/exp_compare_ea_classic_vs_graph.py

"""
Comparison script: Classic EA vs Computational Graph EA
Runs multiple trials and generates comparison plots.
"""

import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np

# Import graph EA via compatibility shim (TestingOnDejongSphereFunction.py provides run_graph_ea)
import ComputationalGraphs.Tests.EATests.TestingOnDejongSphereFunction as graph_ea_module

# Import classic EA
from ClassicEATestOnDeJongSphereFunction import evolve, sphere_function

run_graph_ea = graph_ea_module.run_graph_ea


def run_comparison(
    num_trials=10, pop_size=50, genome_length=5, generations=100, num_elites=1
):
    """
    Run comparison between Classic EA and Graph EA.
    """

    print("=" * 80)
    print(f"COMPARISON: Classic EA vs Computational Graph EA")
    print(
        f"Configuration: DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop"
    )
    print(f"Number of Trials: {num_trials}")
    print("=" * 80)

    classic_results = []
    graph_results = []

    for trial in range(1, num_trials + 1):
        print(f"\n{'='*80}")
        print(f"TRIAL {trial}/{num_trials}")
        print(f"{'='*80}")

        seed = random.randint(0, 1000000)

        random.seed(seed)
        classic_best, classic_fitness, classic_history = evolve(
            sphere_function,
            pop_size=pop_size,
            genome_length=genome_length,
            generations=generations,
            num_elites=num_elites,
            verbose=False,
        )
        classic_results.append(
            {
                "best_fitness": classic_fitness,
                "history": classic_history,
                "solution": classic_best,
            }
        )
        print(f"[Trial {trial}] Classic EA Best Fitness: {classic_fitness:.6f}")

        print(f"[Trial {trial}] Running Computational Graph EA...")
        random.seed(seed)
        graph_best, graph_fitness, graph_history = run_graph_ea(
            pop_size=pop_size,
            genome_length=genome_length,
            generations=generations,
            num_elites=num_elites,
            verbose=False,
        )
        graph_results.append(
            {
                "best_fitness": graph_fitness,
                "history": graph_history,
                "solution": graph_best,
            }
        )
        print(f"[Trial {trial}] Graph EA Best Fitness: {graph_fitness:.6f}")

        save_trial_plot(
            trial,
            classic_history,
            graph_history,
            classic_fitness,
            graph_fitness,
            pop_size,
            genome_length,
            generations,
            num_elites,
        )

    generate_summary(
        classic_results,
        graph_results,
        num_trials,
        pop_size,
        genome_length,
        generations,
        num_elites,
    )

    return classic_results, graph_results


# Rest of file left unchanged for brevity; use the original script in Experiments/ for full functionality
print(
    "\nScript moved: run Experiments/exp_compare_ea_classic_vs_graph.py to execute full comparison"
)

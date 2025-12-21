# Moved from ComputationalGraphs/Tests/EATests/RunClassicEA_MultipleTrials.py
# Renamed to Experiments/exp_run_classic_ea_multitrials.py

"""
Run Classic EA multiple times and generate plots.
"""

import random

import matplotlib.pyplot as plt
import numpy as np

from ClassicEATestOnDeJongSphereFunction import evolve, sphere_function


def run_multiple_trials(
    num_trials=10, pop_size=50, genome_length=5, generations=100, num_elites=1
):
    """Run multiple trials of Classic EA."""

    print("=" * 80)
    print(
        f"Running Classic EA: DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop"
    )
    print(f"Number of Trials: {num_trials}")
    print("=" * 80)

    results = []

    for trial in range(1, num_trials + 1):
        print(f"\nTrial {trial}/{num_trials}...", end=" ")

        best_solution, best_fitness, fitness_history = evolve(
            sphere_function,
            pop_size=pop_size,
            genome_length=genome_length,
            generations=generations,
            num_elites=num_elites,
            verbose=False,
        )

        results.append(
            {
                "trial": trial,
                "best_fitness": best_fitness,
                "history": fitness_history,
                "solution": best_solution,
            }
        )

        print(f"Best: {best_fitness:.6f}")

        # Save individual trial plot
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(fitness_history) + 1), fitness_history, "b-", linewidth=2)
        plt.xlabel("Generation", fontsize=12)
        plt.ylabel("Best Fitness (Lower is Better)", fontsize=12)
        plt.title(
            f"Trial {trial} - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop\nBest: {best_fitness:.6f}",
            fontsize=12,
        )
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filename = f"Trial{trial:02d}_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_Best{best_fitness:.6f}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  → Saved: {filename}")

    # Generate summary
    generate_summary(
        results, num_trials, pop_size, genome_length, generations, num_elites
    )

    return results


# ... rest of file unchanged (retains generate_summary(), main guard, etc.)

print(
    "\nScript moved: run Experiments/exp_run_classic_ea_multitrials.py to execute full experiment"
)

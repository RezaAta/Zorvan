"""
Diagnostics: paired, generation-by-generation comparison of Classic vs Graph EA.

This script runs multiple trials and advances both algorithms one generation at a time
while reseeding the RNG per-generation so both use the same random stream for that
generation. It collects per-generation metrics (best, mean, std, diversity) and
plots the averages across trials. This is designed to expose early-phase differences.
"""

import random

import matplotlib.pyplot as plt
import numpy as np

from ComputationalGraphs.Tests.EATests.TestingOnDejongSphereFunction import run_graph_ea
from Experiments.exp_ea_dejong_sphere import (
    evaluate_population,
    evolve,
    sphere_function,
)


def pop_diversity(pop):
    """Mean pairwise Euclidean distance as a simple diversity metric."""
    arr = np.array(pop)
    n = arr.shape[0]
    if n < 2:
        return 0.0
    # Compute pairwise distances (O(n^2)) - okay for small pop sizes
    dists = []
    for i in range(n):
        for j in range(i + 1, n):
            dists.append(np.linalg.norm(arr[i] - arr[j]))
    return float(np.mean(dists))


def run_diagnostics(
    num_trials=50,
    pop_size=50,
    generations=30,
    genome_length=5,
    num_elites=1,
    verbose=False,
):
    # Containers: metrics per generation per trial
    metrics = {
        "classic_best": np.zeros((num_trials, generations)),
        "graph_best": np.zeros((num_trials, generations)),
        "classic_mean": np.zeros((num_trials, generations)),
        "graph_mean": np.zeros((num_trials, generations)),
        "classic_std": np.zeros((num_trials, generations)),
        "graph_std": np.zeros((num_trials, generations)),
        "classic_div": np.zeros((num_trials, generations)),
        "graph_div": np.zeros((num_trials, generations)),
    }

    # We'll also track per-generation parent→offspring improvement
    metrics["classic_parent_mean"] = np.zeros((num_trials, generations))
    metrics["graph_parent_mean"] = np.zeros((num_trials, generations))
    metrics["classic_offspring_mean"] = np.zeros((num_trials, generations))
    metrics["graph_offspring_mean"] = np.zeros((num_trials, generations))

    for t in range(num_trials):
        # Create paired initial population using a trial seed
        base_seed = random.randint(0, 2**30 - 1)
        random.seed(base_seed)
        initial_population = [
            [random.uniform(-5.12, 5.12) for _ in range(genome_length)]
            for _ in range(pop_size)
        ]

        # Current populations
        classic_pop = [ind[:] for ind in initial_population]
        graph_pop = [ind[:] for ind in initial_population]

        for g in range(generations):
            # Use per-generation deterministic seed so both algorithms see same RNG stream for that gen
            seed_gen = (base_seed + g) & 0xFFFFFFFF

            # Classic: run ONE generation starting from classic_pop
            random.seed(seed_gen)
            # Save parent fitness summary
            parent_fitnesses = evaluate_population(classic_pop, sphere_function)
            metrics["classic_parent_mean"][t, g] = np.mean(parent_fitnesses)

            _, _, _, classic_next_pop = evolve(
                sphere_function,
                pop_size=pop_size,
                genome_length=genome_length,
                generations=1,
                crossover_rate=0.9,
                mutation_rate=0.1,
                mutation_scale=0.1,
                num_elites=num_elites,
                verbose=False,
                initial_population=classic_pop,
                return_population=True,
            )

            # Collect classic metrics for this new generation
            classic_fitnesses = evaluate_population(classic_next_pop, sphere_function)
            metrics["classic_best"][t, g] = np.min(classic_fitnesses)
            metrics["classic_mean"][t, g] = np.mean(classic_fitnesses)
            metrics["classic_std"][t, g] = np.std(classic_fitnesses)
            metrics["classic_div"][t, g] = pop_diversity(classic_next_pop)
            metrics["classic_offspring_mean"][t, g] = np.mean(classic_fitnesses)

            # Graph: run ONE generation (return population)
            random.seed(seed_gen)
            # Save graph parent mean
            parent_fitnesses = evaluate_population(graph_pop, sphere_function)
            metrics["graph_parent_mean"][t, g] = np.mean(parent_fitnesses)

            _b, _bf, _hist, graph_next_pop = run_graph_ea(
                pop_size=pop_size,
                genome_length=genome_length,
                generations=1,
                num_elites=num_elites,
                verbose=False,
                initial_population=graph_pop,
                return_population=True,
            )

            # Collect graph metrics
            graph_fitnesses = evaluate_population(graph_next_pop, sphere_function)
            metrics["graph_best"][t, g] = np.min(graph_fitnesses)
            metrics["graph_mean"][t, g] = np.mean(graph_fitnesses)
            metrics["graph_std"][t, g] = np.std(graph_fitnesses)
            metrics["graph_div"][t, g] = pop_diversity(graph_next_pop)
            metrics["graph_offspring_mean"][t, g] = np.mean(graph_fitnesses)

            # Advance populations
            classic_pop = [ind[:] for ind in classic_next_pop]
            graph_pop = [ind[:] for ind in graph_next_pop]

        if verbose and (t + 1) % max(1, num_trials // 5) == 0:
            print(f"Completed {t+1}/{num_trials} trials")

    # Aggregate (mean ± std across trials) per generation
    results = {}
    for key, arr in metrics.items():
        results[key + "_mean"] = np.mean(arr, axis=0)
        results[key + "_std"] = np.std(arr, axis=0)

    # Fraction of trials per generation where graph_best < classic_best
    # (i.e., graph is better on that generation)
    graph_wins = np.zeros(generations)
    for g in range(generations):
        graph_wins[g] = np.mean(
            metrics["graph_best"][:, g] < metrics["classic_best"][:, g]
        )
    results["graph_advantage_fraction"] = graph_wins

    return results


def plot_diagnostics(results, generations=30, filename_prefix="Diagnostics"):
    gens = np.arange(1, generations + 1)

    # Best fitness comparison (mean ± std)
    plt.figure(figsize=(10, 5))
    plt.plot(gens, results["classic_best_mean"], "b-", label="Classic (best mean)")
    plt.fill_between(
        gens,
        results["classic_best_mean"] - results["classic_best_std"],
        results["classic_best_mean"] + results["classic_best_std"],
        color="blue",
        alpha=0.2,
    )
    plt.plot(gens, results["graph_best_mean"], "g-", label="Graph (best mean)")
    plt.fill_between(
        gens,
        results["graph_best_mean"] - results["graph_best_std"],
        results["graph_best_mean"] + results["graph_best_std"],
        color="green",
        alpha=0.2,
    )
    plt.yscale("log")
    plt.xlabel("Generation")
    plt.ylabel("Best fitness (log scale)")
    plt.title("Diagnostics: Best fitness (mean ± std) per generation")
    plt.legend()
    plt.grid(True, which="both", alpha=0.3)
    fname = f"{filename_prefix}_best_{generations}G.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved plot: {fname}")

    # Diversity comparison
    plt.figure(figsize=(10, 5))
    plt.plot(gens, results["classic_div_mean"], "b-", label="Classic diversity")
    plt.plot(gens, results["graph_div_mean"], "g-", label="Graph diversity")
    plt.xlabel("Generation")
    plt.ylabel("Mean pairwise distance")
    plt.title("Diagnostics: Population diversity per generation")
    plt.legend()
    plt.grid(True, alpha=0.3)
    fname = f"{filename_prefix}_diversity_{generations}G.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved plot: {fname}")

    # Mean fitness comparison
    plt.figure(figsize=(10, 5))
    plt.plot(gens, results["classic_mean_mean"], "b-", label="Classic mean fitness")
    plt.plot(gens, results["graph_mean_mean"], "g-", label="Graph mean fitness")
    plt.xlabel("Generation")
    plt.ylabel("Population mean fitness")
    plt.title("Diagnostics: Population mean fitness per generation")
    plt.legend()
    plt.grid(True, alpha=0.3)
    fname = f"{filename_prefix}_mean_{generations}G.png"
    plt.tight_layout()
    plt.savefig(fname, dpi=150)
    print(f"Saved plot: {fname}")


if __name__ == "__main__":
    res = run_diagnostics(num_trials=50, pop_size=50, generations=30, genome_length=5)
    plot_diagnostics(
        res, generations=30, filename_prefix="Diagnostics_Paired_50trials_30G"
    )
    print("Diagnostics complete. Check generated PNGs for early-generation behavior.")

"""
Comprehensive comparison between Classic EA and Graph EA implementations.
Runs multiple trials of each approach and generates comparison plots.
"""

import matplotlib.pyplot as plt
import numpy as np

from ClassicEATestOnDeJongSphereFunction import evolve, sphere_function
from ComputationalGraphs.Tests.EATests.TestingOnDejongSphereFunction import run_graph_ea


def run_comparison_trials(num_trials=10, pop_size=50, generations=100, num_elites=1):
    """
    Run multiple trials comparing Classic EA vs Graph EA.

    Args:
        num_trials: Number of independent trials to run
        pop_size: Population size
        generations: Number of generations
        num_elites: Number of elite individuals to preserve

    Returns:
        Dictionary with results from both approaches
    """
    print(f"Running Comparison Study: Classic EA vs Graph EA")
    print(
        f"Configuration: {num_trials} trials, {pop_size} pop, {generations} gen, {num_elites} elite(s)"
    )
    print("=" * 80)

    classic_results = {
        "best_fitnesses": [],
        "fitness_histories": [],
        "best_solutions": [],
    }

    graph_results = {
        "best_fitnesses": [],
        "fitness_histories": [],
        "best_solutions": [],
    }

    # Run Classic EA trials
    print("\n[CLASSIC EA TRIALS]")
    print("-" * 80)
    for trial in range(1, num_trials + 1):
        print(f"Classic EA - Trial {trial}/{num_trials}...", end=" ", flush=True)

        best_solution, best_fitness, fitness_history = evolve(
            sphere_function,
            pop_size=pop_size,
            generations=generations,
            num_elites=num_elites,
            verbose=False,
        )

        classic_results["best_fitnesses"].append(best_fitness)
        classic_results["fitness_histories"].append(fitness_history)
        classic_results["best_solutions"].append(best_solution)

        print(f"Best: {best_fitness:.6f}")

    # Run Graph EA trials
    print("\n[GRAPH EA TRIALS]")
    print("-" * 80)
    for trial in range(1, num_trials + 1):
        print(f"Graph EA - Trial {trial}/{num_trials}...", end=" ", flush=True)

        best_solution, best_fitness, fitness_history = run_graph_ea(
            pop_size=pop_size,
            genome_length=5,
            generations=generations,
            num_elites=num_elites,
            verbose=False,
        )

        graph_results["best_fitnesses"].append(best_fitness)
        graph_results["fitness_histories"].append(fitness_history)
        graph_results["best_solutions"].append(best_solution)

        print(f"Best: {best_fitness:.6f}")

    return classic_results, graph_results


def print_statistics(classic_results, graph_results):
    """Print comparison statistics."""
    print("\n" + "=" * 80)
    print("COMPARISON STATISTICS")
    print("=" * 80)

    classic_fits = classic_results["best_fitnesses"]
    graph_fits = graph_results["best_fitnesses"]

    print(f"\n{'Metric':<25} {'Classic EA':<20} {'Graph EA':<20} {'Difference':<15}")
    print("-" * 80)

    # Mean
    classic_mean = np.mean(classic_fits)
    graph_mean = np.mean(graph_fits)
    diff_mean = graph_mean - classic_mean
    print(
        f"{'Mean Fitness':<25} {classic_mean:<20.6f} {graph_mean:<20.6f} {diff_mean:+.6f}"
    )

    # Std Dev
    classic_std = np.std(classic_fits)
    graph_std = np.std(graph_fits)
    diff_std = graph_std - classic_std
    print(
        f"{'Std Deviation':<25} {classic_std:<20.6f} {graph_std:<20.6f} {diff_std:+.6f}"
    )

    # Min
    classic_min = np.min(classic_fits)
    graph_min = np.min(graph_fits)
    diff_min = graph_min - classic_min
    print(
        f"{'Best (Minimum)':<25} {classic_min:<20.6f} {graph_min:<20.6f} {diff_min:+.6f}"
    )

    # Max
    classic_max = np.max(classic_fits)
    graph_max = np.max(graph_fits)
    diff_max = graph_max - classic_max
    print(
        f"{'Worst (Maximum)':<25} {classic_max:<20.6f} {graph_max:<20.6f} {diff_max:+.6f}"
    )

    # Median
    classic_median = np.median(classic_fits)
    graph_median = np.median(graph_fits)
    diff_median = graph_median - classic_median
    print(
        f"{'Median':<25} {classic_median:<20.6f} {graph_median:<20.6f} {diff_median:+.6f}"
    )

    print("=" * 80)

    # Winner determination
    if classic_mean < graph_mean:
        winner = "Classic EA"
        margin = ((graph_mean - classic_mean) / classic_mean) * 100
    elif graph_mean < classic_mean:
        winner = "Graph EA"
        margin = ((classic_mean - graph_mean) / graph_mean) * 100
    else:
        winner = "TIE"
        margin = 0

    print(f"\n🏆 WINNER (by mean fitness): {winner}")
    if winner != "TIE":
        print(f"   Margin: {margin:.2f}% better")
    print("=" * 80)


def generate_comparison_plots(
    classic_results, graph_results, num_trials, pop_size, generations, num_elites
):
    """Generate comprehensive comparison plots."""

    # 1. Box plot comparison
    plt.figure(figsize=(10, 6))
    data = [classic_results["best_fitnesses"], graph_results["best_fitnesses"]]
    bp = plt.boxplot(data, labels=["Classic EA", "Graph EA"], patch_artist=True)
    bp["boxes"][0].set_facecolor("lightblue")
    bp["boxes"][1].set_facecolor("lightgreen")
    plt.ylabel("Best Fitness (Lower is Better)", fontsize=12)
    plt.title(
        f"Fitness Comparison: Classic vs Graph EA\n{num_trials} Trials, {num_elites} Elite, {generations} Gen, {pop_size} Pop",
        fontsize=12,
    )
    plt.grid(True, alpha=0.3, axis="y")
    filename = f"Comparison_BoxPlot_{num_trials}Trials_{num_elites}Elite_{generations}Gen_{pop_size}Pop.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"\n📊 Box plot saved as: {filename}")

    # 2. Convergence curves - Mean ± Std
    plt.figure(figsize=(12, 6))

    # Get max length for histories (they might differ slightly)
    max_gen_classic = max(len(h) for h in classic_results["fitness_histories"])
    max_gen_graph = max(len(h) for h in graph_results["fitness_histories"])
    max_gen = max(max_gen_classic, max_gen_graph)

    # Pad histories to same length if needed
    classic_histories_padded = []
    for hist in classic_results["fitness_histories"]:
        if len(hist) < max_gen:
            padded = hist + [hist[-1]] * (max_gen - len(hist))
        else:
            padded = hist
        classic_histories_padded.append(padded)

    graph_histories_padded = []
    for hist in graph_results["fitness_histories"]:
        if len(hist) < max_gen:
            padded = hist + [hist[-1]] * (max_gen - len(hist))
        else:
            padded = hist
        graph_histories_padded.append(padded)

    # Calculate mean and std
    classic_mean = np.mean(classic_histories_padded, axis=0)
    classic_std = np.std(classic_histories_padded, axis=0)
    graph_mean = np.mean(graph_histories_padded, axis=0)
    graph_std = np.std(graph_histories_padded, axis=0)

    generations_range = range(1, len(classic_mean) + 1)

    # Plot Classic EA
    plt.plot(
        generations_range, classic_mean, "b-", linewidth=2, label="Classic EA (mean)"
    )
    plt.fill_between(
        generations_range,
        classic_mean - classic_std,
        classic_mean + classic_std,
        alpha=0.3,
        color="blue",
    )

    # Plot Graph EA
    plt.plot(generations_range, graph_mean, "g-", linewidth=2, label="Graph EA (mean)")
    plt.fill_between(
        generations_range,
        graph_mean - graph_std,
        graph_mean + graph_std,
        alpha=0.3,
        color="green",
    )

    plt.xlabel("Generation", fontsize=12)
    plt.ylabel("Best Fitness (Lower is Better)", fontsize=12)
    plt.yscale("log")  # Logarithmic scale for better visualization
    plt.title(
        f"Convergence Comparison: Classic vs Graph EA (Mean ± Std)\n{num_trials} Trials, {num_elites} Elite, {generations} Gen, {pop_size} Pop",
        fontsize=12,
    )
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3, which="both")  # Show both major and minor grid lines
    filename = f"Comparison_Convergence_{num_trials}Trials_{num_elites}Elite_{generations}Gen_{pop_size}Pop.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"📈 Convergence plot saved as: {filename}")

    # 3. Individual trials overlay - LOGARITHMIC SCALE
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Classic EA trials
    for i, hist in enumerate(classic_results["fitness_histories"], 1):
        ax1.plot(range(1, len(hist) + 1), hist, alpha=0.5, linewidth=1)
    ax1.plot(
        range(1, len(classic_mean) + 1), classic_mean, "k-", linewidth=3, label="Mean"
    )
    ax1.set_xlabel("Generation", fontsize=11)
    ax1.set_ylabel("Best Fitness (Log Scale)", fontsize=11)
    ax1.set_yscale("log")  # Logarithmic scale
    ax1.set_title(f"Classic EA - All {num_trials} Trials (Log Scale)", fontsize=12)
    ax1.grid(True, alpha=0.3, which="both")
    ax1.legend(fontsize=10, loc="upper right")  # Only show mean in legend

    # Graph EA trials
    for i, hist in enumerate(graph_results["fitness_histories"], 1):
        ax2.plot(range(1, len(hist) + 1), hist, alpha=0.5, linewidth=1)
    ax2.plot(range(1, len(graph_mean) + 1), graph_mean, "k-", linewidth=3, label="Mean")
    ax2.set_xlabel("Generation", fontsize=11)
    ax2.set_ylabel("Best Fitness (Log Scale)", fontsize=11)
    ax2.set_yscale("log")  # Logarithmic scale
    ax2.set_title(f"Graph EA - All {num_trials} Trials (Log Scale)", fontsize=12)
    ax2.grid(True, alpha=0.3, which="both")
    ax2.legend(fontsize=10, loc="upper right")  # Only show mean in legend

    filename = f"Comparison_AllTrials_Log_{num_trials}Trials_{num_elites}Elite_{generations}Gen_{pop_size}Pop.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"📊 All trials plot (log scale) saved as: {filename}")

    # 4. Individual trials overlay - LINEAR SCALE
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Classic EA trials
    for i, hist in enumerate(classic_results["fitness_histories"], 1):
        ax1.plot(range(1, len(hist) + 1), hist, alpha=0.5, linewidth=1)
    ax1.plot(
        range(1, len(classic_mean) + 1), classic_mean, "k-", linewidth=3, label="Mean"
    )
    ax1.set_xlabel("Generation", fontsize=11)
    ax1.set_ylabel("Best Fitness (Linear Scale)", fontsize=11)
    ax1.set_title(f"Classic EA - All {num_trials} Trials (Linear Scale)", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10, loc="upper right")  # Only show mean in legend

    # Graph EA trials
    for i, hist in enumerate(graph_results["fitness_histories"], 1):
        ax2.plot(range(1, len(hist) + 1), hist, alpha=0.5, linewidth=1)
    ax2.plot(range(1, len(graph_mean) + 1), graph_mean, "k-", linewidth=3, label="Mean")
    ax2.set_xlabel("Generation", fontsize=11)
    ax2.set_ylabel("Best Fitness (Linear Scale)", fontsize=11)
    ax2.set_title(f"Graph EA - All {num_trials} Trials (Linear Scale)", fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10, loc="upper right")  # Only show mean in legend

    filename = f"Comparison_AllTrials_Linear_{num_trials}Trials_{num_elites}Elite_{generations}Gen_{pop_size}Pop.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"📊 All trials plot (linear scale) saved as: {filename}")

    # 5. Bar chart - Final statistics
    plt.figure(figsize=(10, 6))
    metrics = ["Mean", "Std Dev", "Best", "Worst", "Median"]
    classic_vals = [
        np.mean(classic_results["best_fitnesses"]),
        np.std(classic_results["best_fitnesses"]),
        np.min(classic_results["best_fitnesses"]),
        np.max(classic_results["best_fitnesses"]),
        np.median(classic_results["best_fitnesses"]),
    ]
    graph_vals = [
        np.mean(graph_results["best_fitnesses"]),
        np.std(graph_results["best_fitnesses"]),
        np.min(graph_results["best_fitnesses"]),
        np.max(graph_results["best_fitnesses"]),
        np.median(graph_results["best_fitnesses"]),
    ]

    x = np.arange(len(metrics))
    width = 0.35

    plt.bar(x - width / 2, classic_vals, width, label="Classic EA", color="lightblue")
    plt.bar(x + width / 2, graph_vals, width, label="Graph EA", color="lightgreen")

    plt.xlabel("Metric", fontsize=12)
    plt.ylabel("Fitness Value", fontsize=12)
    plt.title(
        f"Statistics Comparison: Classic vs Graph EA\n{num_trials} Trials, {num_elites} Elite, {generations} Gen, {pop_size} Pop",
        fontsize=12,
    )
    plt.xticks(x, metrics)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3, axis="y")
    filename = f"Comparison_Statistics_{num_trials}Trials_{num_elites}Elite_{generations}Gen_{pop_size}Pop.png"
    plt.tight_layout()
    plt.savefig(filename, dpi=150)
    print(f"📊 Statistics bar chart saved as: {filename}")

    plt.show()


if __name__ == "__main__":
    # Configuration
    NUM_TRIALS = 1000
    POP_SIZE = 50
    GENERATIONS = 100
    NUM_ELITES = 1

    # Run comparison
    classic_results, graph_results = run_comparison_trials(
        num_trials=NUM_TRIALS,
        pop_size=POP_SIZE,
        generations=GENERATIONS,
        num_elites=NUM_ELITES,
    )

    # Print statistics
    print_statistics(classic_results, graph_results)

    # Generate plots
    generate_comparison_plots(
        classic_results, graph_results, NUM_TRIALS, POP_SIZE, GENERATIONS, NUM_ELITES
    )

    print("\n✅ Comparison study complete!")

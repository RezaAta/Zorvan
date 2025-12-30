from Experiments.exp_compare_ea_classic_vs_graph import (
    print_statistics,
    run_comparison_trials,
)

if __name__ == "__main__":
    classic, graph = run_comparison_trials(
        num_trials=3, pop_size=20, generations=20, num_elites=1, genome_length=5
    )
    print_statistics(classic, graph)
    print("\nPaired initial-population test complete")

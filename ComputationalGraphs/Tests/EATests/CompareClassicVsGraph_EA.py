"""
Comparison script: Classic EA vs Computational Graph EA
Runs multiple trials and generates comparison plots.
"""

import random
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import classic EA
from ClassicEATestOnDeJongSphereFunction import sphere_function, evolve

# Import graph EA - use relative import since we're in the same package
import ComputationalGraphs.Tests.EATests.TestingOnDejongSphereFunction as graph_ea_module
run_graph_ea = graph_ea_module.run_graph_ea


def run_comparison(num_trials=10, pop_size=50, genome_length=5, generations=100, num_elites=1):
    """
    Run comparison between Classic EA and Graph EA.
    
    Args:
        num_trials: Number of independent trials to run
        pop_size: Population size
        genome_length: Genome length
        generations: Number of generations
        num_elites: Number of elite individuals
    """
    
    print("=" * 80)
    print(f"COMPARISON: Classic EA vs Computational Graph EA")
    print(f"Configuration: DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop")
    print(f"Number of Trials: {num_trials}")
    print("=" * 80)
    
    classic_results = []
    graph_results = []
    
    for trial in range(1, num_trials + 1):
        print(f"\n{'='*80}")
        print(f"TRIAL {trial}/{num_trials}")
        print(f"{'='*80}")
        
        # Set seed for reproducibility within comparison
        seed = random.randint(0, 1000000)
        
        # Run Classic EA
        print(f"\n[Trial {trial}] Running Classic EA...")
        random.seed(seed)
        classic_best, classic_fitness, classic_history = evolve(
            sphere_function,
            pop_size=pop_size,
            genome_length=genome_length,
            generations=generations,
            num_elites=num_elites,
            verbose=False
        )
        classic_results.append({
            'best_fitness': classic_fitness,
            'history': classic_history,
            'solution': classic_best
        })
        print(f"[Trial {trial}] Classic EA Best Fitness: {classic_fitness:.6f}")
        
        # Run Graph EA
        print(f"[Trial {trial}] Running Computational Graph EA...")
        random.seed(seed)  # Same seed for fair comparison
        graph_best, graph_fitness, graph_history = run_graph_ea(
            pop_size=pop_size,
            genome_length=genome_length,
            generations=generations,
            num_elites=num_elites,
            verbose=False
        )
        graph_results.append({
            'best_fitness': graph_fitness,
            'history': graph_history,
            'solution': graph_best
        })
        print(f"[Trial {trial}] Graph EA Best Fitness: {graph_fitness:.6f}")
        
        # Save individual trial plot
        save_trial_plot(trial, classic_history, graph_history, classic_fitness, 
                       graph_fitness, pop_size, genome_length, generations, num_elites)
    
    # Generate summary statistics and plots
    generate_summary(classic_results, graph_results, num_trials, pop_size, 
                    genome_length, generations, num_elites)
    
    return classic_results, graph_results


def save_trial_plot(trial_num, classic_history, graph_history, classic_best, 
                    graph_best, pop_size, genome_length, generations, num_elites):
    """Save plot for individual trial."""
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(range(1, len(classic_history) + 1), classic_history, 
             'b-', linewidth=2, label=f'Classic EA (Best: {classic_best:.6f})', alpha=0.7)
    plt.plot(range(1, len(graph_history) + 1), graph_history, 
             'g-', linewidth=2, label=f'Graph EA (Best: {graph_best:.6f})', alpha=0.7)
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Best Fitness (Lower is Better)', fontsize=12)
    plt.title(f'Trial {trial_num} - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop', 
             fontsize=13)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    filename = f"Trial{trial_num}_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_Classic{classic_best:.6f}_Graph{graph_best:.6f}.png"
    plt.savefig(filename, dpi=150)
    plt.close()
    print(f"  → Saved: {filename}")


def generate_summary(classic_results, graph_results, num_trials, pop_size, 
                    genome_length, generations, num_elites):
    """Generate summary statistics and plots."""
    
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")
    
    # Extract best fitnesses
    classic_bests = [r['best_fitness'] for r in classic_results]
    graph_bests = [r['best_fitness'] for r in graph_results]
    
    # Calculate statistics
    classic_mean = np.mean(classic_bests)
    classic_std = np.std(classic_bests)
    classic_min = np.min(classic_bests)
    classic_max = np.max(classic_bests)
    
    graph_mean = np.mean(graph_bests)
    graph_std = np.std(graph_bests)
    graph_min = np.min(graph_bests)
    graph_max = np.max(graph_bests)
    
    print(f"\nClassic EA ({num_trials} trials):")
    print(f"  Mean:   {classic_mean:.6f}")
    print(f"  Std:    {classic_std:.6f}")
    print(f"  Min:    {classic_min:.6f}")
    print(f"  Max:    {classic_max:.6f}")
    
    print(f"\nComputational Graph EA ({num_trials} trials):")
    print(f"  Mean:   {graph_mean:.6f}")
    print(f"  Std:    {graph_std:.6f}")
    print(f"  Min:    {graph_min:.6f}")
    print(f"  Max:    {graph_max:.6f}")
    
    # Plot 1: Box plot comparison
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot
    ax1.boxplot([classic_bests, graph_bests], labels=['Classic EA', 'Graph EA'])
    ax1.set_ylabel('Best Fitness (Lower is Better)', fontsize=11)
    ax1.set_title(f'Best Fitness Distribution\n{num_trials} Trials', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Average convergence curves
    max_gens = min(len(classic_results[0]['history']), len(graph_results[0]['history']))
    classic_avg = np.mean([r['history'][:max_gens] for r in classic_results], axis=0)
    graph_avg = np.mean([r['history'][:max_gens] for r in graph_results], axis=0)
    
    classic_std_curve = np.std([r['history'][:max_gens] for r in classic_results], axis=0)
    graph_std_curve = np.std([r['history'][:max_gens] for r in graph_results], axis=0)
    
    gens = range(1, max_gens + 1)
    ax2.plot(gens, classic_avg, 'b-', linewidth=2, label='Classic EA')
    ax2.fill_between(gens, classic_avg - classic_std_curve, classic_avg + classic_std_curve, 
                     color='blue', alpha=0.2)
    
    ax2.plot(gens, graph_avg, 'g-', linewidth=2, label='Graph EA')
    ax2.fill_between(gens, graph_avg - graph_std_curve, graph_avg + graph_std_curve, 
                     color='green', alpha=0.2)
    
    ax2.set_xlabel('Generation', fontsize=11)
    ax2.set_ylabel('Average Best Fitness', fontsize=11)
    ax2.set_title(f'Average Convergence\n{num_trials} Trials (±1 std)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.suptitle(f'Comparison Summary - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop', 
                fontsize=14, y=1.02)
    plt.tight_layout()
    
    filename = f"Summary_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_{num_trials}Trials.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n→ Summary plot saved: {filename}")
    plt.show()
    
    # Plot 2: All trials overlay
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Classic EA all trials
    for i, result in enumerate(classic_results):
        ax1.plot(range(1, len(result['history']) + 1), result['history'], 
                alpha=0.5, linewidth=1.5, label=f"Trial {i+1} ({result['best_fitness']:.4f})")
    ax1.set_xlabel('Generation', fontsize=11)
    ax1.set_ylabel('Best Fitness', fontsize=11)
    ax1.set_title(f'Classic EA - All {num_trials} Trials', fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=8, ncol=2)
    
    # Graph EA all trials
    for i, result in enumerate(graph_results):
        ax2.plot(range(1, len(result['history']) + 1), result['history'], 
                alpha=0.5, linewidth=1.5, label=f"Trial {i+1} ({result['best_fitness']:.4f})")
    ax2.set_xlabel('Generation', fontsize=11)
    ax2.set_ylabel('Best Fitness', fontsize=11)
    ax2.set_title(f'Graph EA - All {num_trials} Trials', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=8, ncol=2)
    
    plt.suptitle(f'All Trials Overlay - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop', 
                fontsize=14, y=1.00)
    plt.tight_layout()
    
    filename = f"AllTrials_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_{num_trials}Trials.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"→ All trials overlay saved: {filename}")
    plt.show()


if __name__ == "__main__":
    # Configuration
    NUM_TRIALS = 10
    POP_SIZE = 50
    GENOME_LENGTH = 5
    GENERATIONS = 100
    NUM_ELITES = 1
    
    # Run comparison
    classic_results, graph_results = run_comparison(
        num_trials=NUM_TRIALS,
        pop_size=POP_SIZE,
        genome_length=GENOME_LENGTH,
        generations=GENERATIONS,
        num_elites=NUM_ELITES
    )
    
    print(f"\n{'='*80}")
    print("COMPARISON COMPLETE!")
    print(f"Generated {NUM_TRIALS} trial plots + 2 summary plots")
    print(f"{'='*80}")

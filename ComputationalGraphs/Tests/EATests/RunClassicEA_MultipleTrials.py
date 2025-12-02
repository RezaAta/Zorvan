"""
Run Classic EA multiple times and generate plots.
Since the computational graph version requires GUI integration for proper elitism tracking,
this script focuses on the classic implementation.
"""

import random
import matplotlib.pyplot as plt
import numpy as np
from ClassicEATestOnDeJongSphereFunction import sphere_function, evolve


def run_multiple_trials(num_trials=10, pop_size=50, genome_length=5, generations=100, num_elites=1):
    """Run multiple trials of Classic EA."""
    
    print("=" * 80)
    print(f"Running Classic EA: DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop")
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
            verbose=False
        )
        
        results.append({
            'trial': trial,
            'best_fitness': best_fitness,
            'history': fitness_history,
            'solution': best_solution
        })
        
        print(f"Best: {best_fitness:.6f}")
        
        # Save individual trial plot
        plt.figure(figsize=(10, 6))
        plt.plot(range(1, len(fitness_history) + 1), fitness_history, 'b-', linewidth=2)
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Best Fitness (Lower is Better)', fontsize=12)
        plt.title(f'Trial {trial} - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop\nBest: {best_fitness:.6f}', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        filename = f"Trial{trial:02d}_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_Best{best_fitness:.6f}.png"
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"  → Saved: {filename}")
    
    # Generate summary
    generate_summary(results, num_trials, pop_size, genome_length, generations, num_elites)
    
    return results


def generate_summary(results, num_trials, pop_size, genome_length, generations, num_elites):
    """Generate summary statistics and plots."""
    
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")
    
    # Extract best fitnesses
    bests = [r['best_fitness'] for r in results]
    
    # Calculate statistics
    mean_fitness = np.mean(bests)
    std_fitness = np.std(bests)
    min_fitness = np.min(bests)
    max_fitness = np.max(bests)
    median_fitness = np.median(bests)
    
    print(f"\nBest Fitness Statistics ({num_trials} trials):")
    print(f"  Mean:    {mean_fitness:.6f}")
    print(f"  Std Dev: {std_fitness:.6f}")
    print(f"  Min:     {min_fitness:.6f}")
    print(f"  Max:     {max_fitness:.6f}")
    print(f"  Median:  {median_fitness:.6f}")
    
    # Plot 1: Box plot and histogram
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Box plot
    ax1.boxplot([bests], labels=['Classic EA'])
    ax1.set_ylabel('Best Fitness (Lower is Better)', fontsize=11)
    ax1.set_title(f'Best Fitness Distribution\n{num_trials} Trials', fontsize=12)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Histogram
    ax2.hist(bests, bins=min(10, num_trials//2 + 1), edgecolor='black', alpha=0.7)
    ax2.axvline(mean_fitness, color='r', linestyle='--', linewidth=2, label=f'Mean: {mean_fitness:.6f}')
    ax2.axvline(median_fitness, color='g', linestyle='--', linewidth=2, label=f'Median: {median_fitness:.6f}')
    ax2.set_xlabel('Best Fitness', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.set_title('Fitness Distribution', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle(f'Summary Statistics - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop', 
                fontsize=14, y=1.02)
    plt.tight_layout()
    
    filename = f"Summary_Stats_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_{num_trials}Trials.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n→ Summary statistics plot saved: {filename}")
    plt.close()
    
    # Plot 2: Average convergence curve
    max_gens = min(len(r['history']) for r in results)
    histories = np.array([r['history'][:max_gens] for r in results])
    
    mean_curve = np.mean(histories, axis=0)
    std_curve = np.std(histories, axis=0)
    min_curve = np.min(histories, axis=0)
    max_curve = np.max(histories, axis=0)
    
    plt.figure(figsize=(12, 7))
    
    gens = range(1, max_gens + 1)
    
    # Plot mean with confidence interval
    plt.plot(gens, mean_curve, 'b-', linewidth=2.5, label='Mean')
    plt.fill_between(gens, mean_curve - std_curve, mean_curve + std_curve, 
                     color='blue', alpha=0.2, label='±1 Std Dev')
    plt.fill_between(gens, min_curve, max_curve, 
                     color='lightblue', alpha=0.3, label='Min-Max Range')
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Best Fitness (Lower is Better)', fontsize=12)
    plt.title(f'Average Convergence - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop\n{num_trials} Trials', 
             fontsize=13)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    filename = f"Convergence_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_{num_trials}Trials.png"
    plt.savefig(filename, dpi=150)
    print(f"→ Convergence plot saved: {filename}")
    plt.close()
    
    # Plot 3: All trials overlay
    plt.figure(figsize=(14, 8))
    
    for result in results:
        plt.plot(range(1, len(result['history']) + 1), result['history'], 
                alpha=0.6, linewidth=1.5, label=f"Trial {result['trial']} ({result['best_fitness']:.4f})")
    
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Best Fitness', fontsize=12)
    plt.title(f'All {num_trials} Trials Overlay - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop', 
             fontsize=13)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9, ncol=2, loc='best')
    plt.tight_layout()
    
    filename = f"AllTrials_DeJong_{num_elites}Elite_{generations}Gen_{pop_size}Pop_{num_trials}Trials.png"
    plt.savefig(filename, dpi=150)
    print(f"→ All trials overlay saved: {filename}")
    plt.show()  # Show the last plot
    
    # Print trial details table
    print(f"\n{'='*80}")
    print("TRIAL DETAILS")
    print(f"{'='*80}")
    print(f"{'Trial':<8} {'Best Fitness':<15} {'Improvement':<15}")
    print(f"{'-'*8} {'-'*15} {'-'*15}")
    for r in results:
        improvement = r['history'][0] - r['history'][-1]
        print(f"{r['trial']:<8} {r['best_fitness']:<15.6f} {improvement:<15.6f}")


if __name__ == "__main__":
    # Configuration
    NUM_TRIALS = 10
    POP_SIZE = 50
    GENOME_LENGTH = 5
    GENERATIONS = 100
    NUM_ELITES = 1
    
    # Run multiple trials
    results = run_multiple_trials(
        num_trials=NUM_TRIALS,
        pop_size=POP_SIZE,
        genome_length=GENOME_LENGTH,
        generations=GENERATIONS,
        num_elites=NUM_ELITES
    )
    
    print(f"\n{'='*80}")
    print(f"COMPLETE! Generated {NUM_TRIALS} trial plots + 3 summary plots")
    print(f"{'='*80}")

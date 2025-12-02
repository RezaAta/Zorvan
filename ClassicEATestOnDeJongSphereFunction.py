import random

def sphere_function(x):
    return sum(i ** 2 for i in x)

def create_population(pop_size, genome_length, lower=-5.12, upper=5.12):
    return [[random.uniform(lower, upper) for _ in range(genome_length)] for _ in range(pop_size)]

def evaluate_population(pop, fitness_fn):
    return [fitness_fn(ind) for ind in pop]

def tournament_selection(pop, fitnesses, k=3):
    selected = []
    for _ in range(2):
        candidates = random.sample(list(zip(pop, fitnesses)), k)
        selected.append(min(candidates, key=lambda x: x[1])[0])
    return selected

def crossover(p1, p2, rate=0.9):
    if random.random() > rate:
        return p1[:], p2[:]
    point = random.randint(1, len(p1) - 2)
    return p1[:point] + p2[point:], p2[:point] + p1[point:]

def mutate(ind, rate=0.1, scale=0.1):
    return [gene + random.gauss(0, scale) if random.random() < rate else gene for gene in ind]

def evolve(
    fitness_fn,
    pop_size=50,
    genome_length=5,
    generations=100,
    crossover_rate=0.9,
    mutation_rate=0.1,
    mutation_scale=0.1,
    num_elites=1,
    verbose=True
):
    population = create_population(pop_size, genome_length)
    best_fitness_history = []
    
    for gen in range(generations):
        fitnesses = evaluate_population(population, fitness_fn)
        best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        best_fitness_history.append(fitnesses[best_idx])
        
        if verbose:
            print(f"Gen {gen}: Best Fitness = {fitnesses[best_idx]:.4f}")

        # Elitism: keep best N individuals
        sorted_indices = sorted(range(len(fitnesses)), key=lambda i: fitnesses[i])
        new_population = [population[i] for i in sorted_indices[:num_elites]]
        
        # Generate offspring to fill remaining population
        while len(new_population) < pop_size:
            p1, p2 = tournament_selection(population, fitnesses)
            c1, c2 = crossover(p1, p2, crossover_rate)
            new_population.append(mutate(c1, mutation_rate, mutation_scale))
            if len(new_population) < pop_size:
                new_population.append(mutate(c2, mutation_rate, mutation_scale))
        population = new_population[:pop_size]  # Ensure exact size
    
    # Final evaluation
    fitnesses = evaluate_population(population, fitness_fn)
    best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
    
    return population[best_idx], fitnesses[best_idx], best_fitness_history


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # Configuration
    pop_size = 50
    genome_length = 5
    generations = 100
    num_elites = 1
    
    print(f"Running Classic EA: DeJong Sphere, {num_elites} elite(s), {generations} gen, {pop_size} pop")
    print("=" * 70)
    
    best_solution, best_fitness, fitness_history = evolve(
        sphere_function,
        pop_size=pop_size,
        genome_length=genome_length,
        generations=generations,
        num_elites=num_elites,
        verbose=True
    )
    
    print("=" * 70)
    print(f"Best solution: {best_solution}")
    print(f"Best fitness: {best_fitness:.6f}")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(fitness_history) + 1), fitness_history, 'b-', linewidth=2, label='Best Fitness')
    plt.xlabel('Generation', fontsize=12)
    plt.ylabel('Fitness (Lower is Better)', fontsize=12)
    plt.yscale('log')  # Logarithmic scale for better visualization
    plt.title(f'Classic EA - DeJong Sphere, {num_elites} Elite, {generations} Gen, {pop_size} Pop\nBest: {best_fitness:.6f}', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    # Save plot
    filename = f"Classic_DeJong_Sphere_{num_elites}Elite_{generations}Gen_{pop_size}Pop_Best{best_fitness:.6f}.png"
    plt.savefig(filename, dpi=150)
    print(f"Plot saved as: {filename}")
    plt.show()

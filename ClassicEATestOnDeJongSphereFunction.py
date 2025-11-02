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
):
    population = create_population(pop_size, genome_length)
    for gen in range(generations):
        fitnesses = evaluate_population(population, fitness_fn)
        best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        print(f"Gen {gen}: Best Fitness = {fitnesses[best_idx]:.4f}")

        # new_population = [population[best_idx]]  # elitism
        new_population = []  # No elitism
        while len(new_population) < pop_size:
            p1, p2 = tournament_selection(population, fitnesses)
            c1, c2 = crossover(p1, p2, crossover_rate)
            new_population.append(mutate(c1, mutation_rate, mutation_scale))
            if len(new_population) < pop_size:
                new_population.append(mutate(c2, mutation_rate, mutation_scale))
        population = new_population
    return population[best_idx], fitnesses[best_idx]


best_solution, best_fitness = evolve(sphere_function)
print("Best solution:", best_solution)
print("Best fitness:", best_fitness)

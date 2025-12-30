import importlib.util
import os
import random

HERE = os.path.dirname(__file__)
TARGET = os.path.join(HERE, "..", "Experiments", "exp_graph_ea_dejong_sphere.py")
TARGET = os.path.normpath(TARGET)
spec = importlib.util.spec_from_file_location("exp_graph_ea_dejong_sphere", TARGET)
graph_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_mod)

# We'll replicate a few trials and check that the initial_population constructed
# in the comparison routine is identical to the population seen by the graph

random.seed(12345)
NUM_TRIALS = 5
POP_SIZE = 20
GENOME_LENGTH = 5

mismatch_found = False
for t in range(1, NUM_TRIALS + 1):
    seed = random.randint(0, 1000000)
    random.seed(seed)
    initial_population = [
        [random.uniform(-5.12, 5.12) for _ in range(GENOME_LENGTH)]
        for _ in range(POP_SIZE)
    ]

    # Pass initial_population to graph with debug flag to capture its initial buffer
    result = graph_mod.run_graph_ea(
        pop_size=POP_SIZE,
        genome_length=GENOME_LENGTH,
        generations=1,
        num_elites=1,
        verbose=False,
        initial_population=initial_population,
        debug_return_initial=True,
    )

    # Unpack depending on returned structure
    if len(result) == 5:
        _, _, _, final_pop, graph_initial = result
    else:
        _, _, _, final_pop = result
        graph_initial = None

    # Compare element-wise (values may be identical floats)
    if graph_initial is None:
        print(f"Trial {t}: could not retrieve graph initial buffer")
        mismatch_found = True
        continue

    # Normalize both: convert nested lists to tuples for comparison
    ip = [tuple(map(float, ind)) for ind in initial_population]
    gp = []
    for x in graph_initial:
        if x is None:
            gp.append(None)
        else:
            gp.append(tuple(map(float, x)))

    # Find first difference
    if len(gp) < len(ip):
        print(f"Trial {t}: graph initial shorter")
        mismatch_found = True
    else:
        for i, (a, b) in enumerate(zip(ip, gp)):
            if b is None:
                print(
                    f"Trial {t}: graph initial at index {i} is None while expected genome"
                )
                mismatch_found = True
                break
            if any(abs(va - vb) > 1e-12 for va, vb in zip(a, b)):
                print(
                    f"Trial {t}: mismatch at index {i}: classic {a[:3]}..., graph {b[:3]}..."
                )
                mismatch_found = True
                break

if not mismatch_found:
    print("All trials: initial populations match exactly (element-wise)")
else:
    print("Mismatches found; see messages above")

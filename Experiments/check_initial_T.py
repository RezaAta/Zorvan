"""Quick check: sample initial T produced by RNG used in experiments."""

import statistics

import numpy as np


def sample_initial_T(seeds):
    vals = []
    for s in seeds:
        rng = np.random.RandomState(s)
        _ = rng.uniform(-10.0, 35.0)
        _ = rng.uniform(0.01, 0.12)
        _ = rng.uniform(0.05, 0.5)
        vals.append(rng.uniform(5.0, 25.0))
    return vals


if __name__ == "__main__":
    seeds = [0, 1, 2, 3, 4, 5, 10, 20, 30, 40, 50, 99]
    vals = sample_initial_T(seeds)
    for s, v in zip(seeds, vals):
        print(s, v)

    many = sample_initial_T(range(1000))
    print("min", min(many), "max", max(many), "mean", statistics.mean(many))

import os
import sys

# Ensure project root is on sys.path so Experiments package can be imported
sys.path.insert(0, os.getcwd())
from Experiments.exp_ea_diagnostics import plot_diagnostics, run_diagnostics

if __name__ == "__main__":
    res = run_diagnostics(
        num_trials=20,
        pop_size=50,
        generations=30,
        genome_length=5,
        num_elites=1,
        verbose=True,
    )
    plot_diagnostics(
        res, generations=30, filename_prefix="Diagnostics_Test_20trials_30G"
    )
    print("Done")

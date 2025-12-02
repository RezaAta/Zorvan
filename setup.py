from pathlib import Path

from setuptools import find_packages, setup


def read_requirements(filename="requirements.txt"):
    p = Path(__file__).parent / filename
    if not p.exists():
        return []
    reqs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        reqs.append(line)
    return reqs


install_requires = read_requirements()


setup(
    name="ComputationalGraphs",
    version="0.1.0",
    packages=find_packages(),
    # Export some useful top-level scripts as modules so they are importable
    # after `pip install -e .` (tests reference them as plain imports).
    py_modules=[
        "ClassicMLP",
        "ClassicEATestOnDeJongSphereFunction",
        "ClassicFuzzySystemOnFanControlProblem",
    ],
    description="A python package to create and run computational graphs.",
    author="Reza Ataei",
    author_email="reza.a1999@yahoo.com",
    url="https://github.com/RezaAta/ComputationalGraphs.git",
    python_requires=">=3.8",
    install_requires=install_requires,
    include_package_data=True,
)

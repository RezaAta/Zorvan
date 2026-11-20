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
    name="zorvan-reference",
    version="0.1.0",
    packages=find_packages(where="reference"),
    package_dir={"": "reference"},
    description="A Python framework for building and running computational graphs.",
    author="Zorvan contributors",
    url="https://github.com/RezaAta/Zorvan",
    python_requires=">=3.8",
    install_requires=install_requires,
    include_package_data=True,
)

from setuptools import setup, find_packages

setup(
    name="ComputationalGraphs",  # Name of your library
    version="0.1",
    packages=find_packages(),
    description="A library of computational graph node classes",
    author="Reza Ataei",
    author_email="reza.a1999@yahoo.com",
    url="https://github.com/RezaAta/ComputationalGraphs.git",  # If you host it on GitHub
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

import os

dirs = [
    "atlas-core/atlas/topology",
    "atlas-core/atlas/hashing",
    "atlas-core/atlas/privacy",
    "atlas-core/atlas/protocol",
    "atlas-core/tests"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    if "atlas/" in d:
        with open(os.path.join(d, "__init__.py"), "w") as f:
            f.write("# Initialize module\n")

# Main init
with open("atlas-core/atlas/__init__.py", "w") as f:
    f.write('__version__ = "0.1.0"\n')

# setup.py
setup_py = """
from setuptools import setup, find_packages

setup(
    name="atlas-core",
    version="0.1.0",
    description="Core libraries for the Topology Interchange Protocol (TIP)",
    author="ATLAS Consortium",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.26.0",
        "scikit-learn>=1.3.0",
        "torch>=2.0.0",
        "giotto-tda>=0.6.0",
    ],
)
"""
with open("atlas-core/setup.py", "w") as f:
    f.write(setup_py.strip() + "\n")

# README.md
readme = """
# ATLAS Core

The reference implementation of the Topology Interchange Protocol (TIP).

## Modules
- `atlas.topology`: Topological extraction and vectorization (Persistence Images).
- `atlas.hashing`: Locality-Sensitive Hashing (LSH) for topological signatures.
- `atlas.privacy`: Latent Privacy Layer (LPL) implementing Adversarial Autoencoders for property disentanglement.
- `atlas.protocol`: Message formatting and routing for federated metadata exchange.
"""
with open("atlas-core/README.md", "w") as f:
    f.write(readme.strip() + "\n")

print("Scaffolding complete.")

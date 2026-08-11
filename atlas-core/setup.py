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

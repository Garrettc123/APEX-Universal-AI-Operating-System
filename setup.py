from setuptools import setup, find_packages

setup(
    name="apex-universal-ai-os",
    version="1.0.0",
    description="APEX Universal AI Operating System - Self-evolving superintelligence",
    author="Garrett C",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "asyncio>=3.4.3",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Programming Language :: Python :: 3.8",
    ],
)

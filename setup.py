#!/usr/bin/env python3
"""
Setup script for equitrcoder - Modular AI coding assistant.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="equitrcoder",
    version="2.3.0",
    description="Modular AI coding assistant supporting single and multi-agent workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="EQUITR",
    author_email="tanushvanarase@equitr.com",
    url="https://github.com/tanushv/equitrcoder",
    packages=find_packages(include=["equitrcoder", "equitrcoder.*"]),
    include_package_data=True,
    package_data={
        "equitrcoder": [
            "config/*.yaml",
            "**/*.yaml",
            "**/*.json",
        ]
    },
    install_requires=requirements,
    extras_require={
        "api": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
        ],
        "tui": [
            "textual>=0.45.0",
            "rich>=13.0.0",
        ],
        "mcp": [
            "mcp>=0.1.0",
        ],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.6.0",
            "isort>=5.12.0",
        ],
        "all": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0", 
            "textual>=0.45.0",
            "rich>=13.0.0",
            "mcp>=0.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "equitrcoder=equitrcoder.cli.unified_main:main",
            "equitr=equitrcoder.cli.unified_main:main",  # Short alias
        ]
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    keywords="ai coding assistant agent multi-agent llm automation",
    project_urls={
        "Bug Reports": "https://github.com/equitr/equitrcoder/issues",
        "Source": "https://github.com/equitr/equitrcoder",
        "Documentation": "https://equitrcoder.readthedocs.io/",
    },
)

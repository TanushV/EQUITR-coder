from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="equitrcoder-multi-agent",
    version="1.0.0",
    author="EQUITR-coder Team",
    author_email="team@equitrcoder.ai",
    description="Multi-agent workflow system with optional strong/weak model architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equitrcoder/multi-agent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pytest>=6.0",
        "pytest-asyncio>=0.21.0",
    ],
    extras_require={
        "dev": [
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "equitrcoder=src.cli.main_cli:main",
        ],
    },
)

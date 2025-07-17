"""
Setup script for EquitrCoder
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="equitrcoder",
    version="1.0.0",
    author="EQUITR Team",
    author_email="team@equitr.ai",
    description="AI-powered coding assistant for modern development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/equitr/equitrcoder",
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
    ],
    python_requires=">=3.8",
    install_requires=[
        "litellm>=1.0.0",
        "aiofiles>=23.0.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "equitrcoder=equitrcoder.cli:main_sync",
        ],
    },
)

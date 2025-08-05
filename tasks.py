"""
Build and development tasks for Mario Game.
"""

from invoke import task
import os
import sys

@task
def run(c):
    """Run the game."""
    c.run("python -m game.main")

@task
def test(c):
    """Run tests."""
    c.run("pytest tests/ -v")

@task
def test_coverage(c):
    """Run tests with coverage."""
    c.run("pytest tests/ --cov=game --cov-report=html --cov-report=term-missing")

@task
def lint(c):
    """Run linting."""
    c.run("flake8 game tests")

@task
def format(c):
    """Format code with black and isort."""
    c.run("black game tests")
    c.run("isort game tests")

@task
def format_check(c):
    """Check code formatting."""
    c.run("black --check game tests")
    c.run("isort --check-only game tests")

@task
def clean(c):
    """Clean build artifacts."""
    c.run("rm -rf build/ dist/ *.egg-info/")
    c.run("rm -rf .pytest_cache/ .coverage htmlcov/")
    c.run("find . -type d -name __pycache__ -exec rm -rf {} +")
    c.run("find . -type f -name "*.pyc" -delete")

@task
def setup(c):
    """Set up development environment."""
    c.run("pip install -r requirements.txt")
    c.run("pip install -r requirements-dev.txt")
    c.run("pre-commit install")

@task
def build(c):
    """Build the package."""
    c.run("python -m build")

@task
def all(c):
    """Run all checks: format, lint, test."""
    format_check(c)
    lint(c)
    test(c)
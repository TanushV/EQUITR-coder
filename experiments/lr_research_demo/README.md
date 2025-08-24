# Linear Regression Research Demo

This folder contains a mostly-finished mini-project to run two linear regression experiments on a simple, randomly generated correlated dataset. It is designed to be completed by EQUITR Coder Research Mode.

- `requirements.txt`: minimal dependencies for experiments
- `runner.py`: programmatic entrypoint that invokes Research Mode on this folder

Usage:

1. Ensure your API keys are set for your chosen model provider.
2. From repo root:
   ```bash
   python3 experiments/lr_research_demo/runner.py
   ```

Environment setup (Linux / macOS)

1. Create a Python 3.11 virtual environment and install runtime dependencies:

   ```bash
   make venv
   make install
   ```

2. (Optional) Install development tools (linters, formatters, test runner):

   ```bash
   make install_dev
   ```

3. (Optional) Install and enable pre-commit hooks:

   ```bash
   make install_precommit
   ```

Useful Make targets

- `make venv` - create a `.venv` using python3.11 and update pip
- `make install` - install runtime dependencies from `requirements.txt` into the venv
- `make install_dev` - install dev dependencies from `requirements-dev.txt`
- `make install_precommit` - install pre-commit and register hooks
- `make lint` - run ruff, black (check), isort (check), flake8, and mypy
- `make fmt` - auto-format with ruff/isort/black
- `make test` - runs the test target (currently a placeholder)
- `make clean` - remove the venv and caches

CI and pre-commit

- A GitHub Actions workflow is provided at `.github/workflows/ci.yml` to run linting and basic checks on push and pull_request. It assumes the Makefile targets above are available.
- Pre-commit configuration is provided in `.pre-commit-config.yaml` and can be installed using `make install_precommit` or `./scripts/install_precommit.sh`.

Notes

- All development files (venv, caches) are ignored by `.gitignore`.
- The repo pins runtime dependencies in `requirements.txt` and keeps dev dependencies in `requirements-dev.txt` for determinism.

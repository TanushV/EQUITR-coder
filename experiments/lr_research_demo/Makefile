PY ?= python3.11
VENV ?= .venv
PIP = $(VENV)/bin/pip
PYBIN = $(VENV)/bin/python

.PHONY: venv install install_dev install_precommit lint fmt test clean

venv:
	$(PY) -m venv $(VENV)
	$(VENV)/bin/pip install -U pip==24.2

install: venv
	$(PIP) install -r requirements.txt

install_dev: venv
	$(PIP) install -r requirements-dev.txt

install_precommit: install_dev
	$(PYBIN) -m pip install pre-commit
	$(PYBIN) -m pre_commit install || true

lint: install_dev
	$(PYBIN) -m ruff .
	$(PYBIN) -m black --check .
	$(PYBIN) -m isort --check-only .
	$(PYBIN) -m flake8 .
	$(PYBIN) -m mypy . || true

fmt: install_dev
	$(PYBIN) -m ruff . --fix
	$(PYBIN) -m isort .
	$(PYBIN) -m black .

test: install_dev
	# No tests yet; placeholder. Add pytest tests/ when available.
	@echo "No tests to run"

clean:
	rm -rf $(VENV) .pytest_cache .mypy_cache

PYTHON=python3.9
VENV=.venv

.PHONY: venv run test lint clean

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt

run:
	$(VENV)/bin/python -m game.main

test:
	$(VENV)/bin/pytest

lint:
	$(VENV)/bin/black game tests
	$(VENV)/bin/flake8 game tests

clean:
	rm -rf $(VENV) __pycache__ .pytest_cache

.DEFAULT: help

VENV ?= venv
PYTHON = $(VENV)/bin/python3
PIP = $(PYTHON) -m pip

help:
	@echo "use: make [venv | install | clean | build | upload]"

venv: $(VENV)/bin/activate
$(VENV)/bin/activate: setup.py requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install:
	$(PIP) install .

clean: clean-build clean-pyc

clean-build:
	rm -rf build/
	rm -rf dist/*
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.DS_Store' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

build: clean
	$(PYTHON) setup.py sdist

upload:
	twine upload dist/*

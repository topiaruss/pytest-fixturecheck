.PHONY: clean install test test-all test-specific lint mypy format build publish tox pre-commit

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .tox/ __pycache__/ */__pycache__/ */*/__pycache__/

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest -xvs

test-all:
	pytest -xvs tests/

test-specific:
	pytest -xvs $(filter-out $@,$(MAKECMDGOALS))

lint:
	flake8 src tests

mypy:
	mypy src

format:
	isort src tests
	black src tests

pre-commit:
	pre-commit run --all-files

tox:
	tox

tox-py37:
	tox -e py37

tox-py38:
	tox -e py38

tox-py39:
	tox -e py39

tox-py310:
	tox -e py310

tox-py311:
	tox -e py311

tox-lint:
	tox -e lint

tox-mypy:
	tox -e mypy

tox-django:
	tox -e django

build:
	python -m build

publish:
	twine upload dist/*

%:
	@:

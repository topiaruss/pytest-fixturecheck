.PHONY: clean install test test-all test-specific lint mypy format build publish tox pre-commit version-patch version-minor version-major release tag

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

# Use the virtual environment python if it exists, otherwise try system python
build:
	(test -f .venv/bin/python && .venv/bin/python -m build) || \
	(test -f env/bin/python && env/bin/python -m build) || \
	(python3 -m build)

# Upload to PyPI using the same Python as build
publish:
	(test -f .venv/bin/python && .venv/bin/python -m twine upload dist/*) || \
	(test -f env/bin/python && env/bin/python -m twine upload dist/*) || \
	(python3 -m twine upload dist/*)

# Tag the current version and push the tag
tag:
	VERSION=$$(grep -m 1 "version" pyproject.toml | sed 's/.*"\(.*\)".*/\1/'); \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push --tags

# Full release process: build, publish and tag
release: clean build publish tag
	@echo "Release process completed!"

version-patch:
	python scripts/bump_version.py patch

version-minor:
	python scripts/bump_version.py minor

version-major:
	python scripts/bump_version.py major

%:
	@:

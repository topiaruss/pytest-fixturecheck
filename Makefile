# pytest-fixturecheck Makefile
#
# Environment Variables for Release:
#   UV_PUBLISH_TOKEN - PyPI API token for publishing (get from https://pypi.org/manage/account/#api-tokens)
#
# Usage:
#   make build         - Build the package
#   make publish-test  - Publish to TestPyPI 
#   make publish       - Publish to PyPI
#   make release       - Full release process

.PHONY: clean install install-dev test test-all test-specific check format mypy build publish publish-test tox pre-commit version-patch version-minor version-major release tag update-badge

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .tox/ __pycache__/ */__pycache__/ */*/__pycache__/

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	PYTHONPATH=src pytest -xvs

test-all:
	PYTHONPATH=src pytest -xvs tests/

test-specific:
	PYTHONPATH=src pytest -xvs $(filter-out $@,$(MAKECMDGOALS))

check:
	ruff check src tests

format:
	ruff format src tests

mypy:
	mypy src

pre-commit:
	pre-commit run --all-files

tox:
	tox

# Update the PyPI badge in README.md to match the current version
update-badge:
	python3 scripts/update_badge.py

build:
	uv build

publish:
	uv publish

publish-test:
	uv publish --publish-url https://test.pypi.org/legacy/

tag:
	VERSION=$$(grep -m 1 "version" pyproject.toml | sed 's/.*"\(.*\)".*/\1/'); \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push --tags

release: update-badge clean build publish tag
	@echo "Release process completed!"

version-patch:
	python scripts/bump_version.py patch

version-minor:
	python scripts/bump_version.py minor

version-major:
	python scripts/bump_version.py major

%:
	@:

# pytest-fixturecheck Makefile
#
# Environment Variables for Release:
#   UV_PUBLISH_TOKEN - PyPI API token for publishing (get from https://pypi.org/manage/account/#api-tokens)
#
# Usage:
#   make sync          - Install and sync dependencies
#   make build         - Build the package
#   make publish-test  - Publish to TestPyPI 
#   make publish       - Publish to PyPI
#   make release       - Full release process

.PHONY: clean sync install install-dev test test-all test-specific check format mypy build publish publish-test tox pre-commit version-patch version-minor version-major release tag update-badge

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage htmlcov/ .tox/ __pycache__/ */__pycache__/ */*/__pycache__/

sync:
	uv sync

install:
	uv sync --no-dev

install-dev:
	uv sync

test:
	uv run pytest -xvs

test-all:
	uv run pytest -xvs tests/

test-specific:
	uv run pytest -xvs $(filter-out $@,$(MAKECMDGOALS))

check:
	uv run ruff check src tests

format:
	uv run ruff format src tests

mypy:
	uv run mypy src

pre-commit:
	uv run pre-commit run --all-files

tox:
	tox

# Update the PyPI badge in README.md to match the current version
update-badge:
	uv run python scripts/update_badge.py

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
	uv run python scripts/bump_version.py patch

version-minor:
	uv run python scripts/bump_version.py minor

version-major:
	uv run python scripts/bump_version.py major

%:
	@:

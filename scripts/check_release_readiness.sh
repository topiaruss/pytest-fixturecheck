#!/bin/bash
# Script to check if the repository is ready for release
# Usage: ./scripts/check_release_readiness.sh [version]

echo "=== Checking release readiness for version ${1:-UNKNOWN} ==="

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
  echo "❌ ERROR: There are uncommitted changes:"
  git status -s
  echo ""
  echo "You should commit or stash these changes before release."
  exit 1
else
  echo "✅ No uncommitted changes."
fi

# Ensure we are on the main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" ]]; then
  echo "❌ ERROR: Not on main branch. Currently on: $CURRENT_BRANCH"
  exit 1
else
  echo "✅ On main branch."
fi

# Check if all tests pass
echo "Running tests..."
if ! make test-all; then
  echo "❌ ERROR: Tests failed."
  exit 1
else
  echo "✅ All tests pass."
fi

# Check if version number in pyproject.toml matches tag
VERSION=${1:-"0.0.0"}
if [[ "$VERSION" != "0.0.0" ]]; then
  TOML_VERSION=$(grep -o 'version = "[^"]*' pyproject.toml | cut -d'"' -f2)
  if [[ "$TOML_VERSION" != "$VERSION" ]]; then
    echo "❌ ERROR: Version in pyproject.toml ($TOML_VERSION) doesn't match release version ($VERSION)"
    exit 1
  else
    echo "✅ Version in pyproject.toml matches release version."
  fi
fi

echo "✅ Repository is ready for release."
echo ""
echo "Next steps:"
echo "1. git tag -a v${VERSION} -m \"Version ${VERSION}\""
echo "2. git push origin main"
echo "3. git push origin v${VERSION}"
echo "4. python -m build"
echo "5. python -m twine upload dist/*" 
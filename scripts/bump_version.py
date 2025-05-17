#!/usr/bin/env python
"""
Bump the version in pyproject.toml and src/pytest_fixturecheck/__init__.py
"""

import re
import sys
import subprocess
from pathlib import Path

INIT_FILE = "src/pytest_fixturecheck/__init__.py"
PYPROJECT_FILE = "pyproject.toml"


def get_current_version():
    """Extract the current version from pyproject.toml."""
    pyproject_path = Path(PYPROJECT_FILE)

    if not pyproject_path.exists():
        print(f"Error: {PYPROJECT_FILE} not found")
        sys.exit(1)

    with open(pyproject_path, "r") as f:
        content = f.read()

    # Find the version line
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        print(f"Error: Could not find version in {PYPROJECT_FILE}")
        sys.exit(1)

    return version_match.group(1)


def bump_version(current_version, bump_type):
    """Bump the version according to the bump_type (patch, minor, major)."""
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == "patch":
        patch += 1
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    else:
        print(
            f"Error: Invalid bump type '{bump_type}'. Must be 'patch', 'minor', or 'major'."
        )
        sys.exit(1)

    return f"{major}.{minor}.{patch}"


def update_pyproject(new_version):
    """Update the version in pyproject.toml."""
    with open(PYPROJECT_FILE, "r") as f:
        content = f.read()

    # Replace the version
    updated_content = re.sub(
        r'(version\s*=\s*)"[^"]+"', r'\1"' + new_version + '"', content
    )

    with open(PYPROJECT_FILE, "w") as f:
        f.write(updated_content)

    print(f"Updated {PYPROJECT_FILE} to version {new_version}")


def update_init(new_version):
    """Update the version in __init__.py."""
    init_path = Path(INIT_FILE)

    if not init_path.exists():
        print(f"Warning: {INIT_FILE} not found, skipping")
        return

    with open(init_path, "r") as f:
        content = f.read()

    # Replace the version
    updated_content = re.sub(
        r'(__version__\s*=\s*)"[^"]+"', r'\1"' + new_version + '"', content
    )

    with open(init_path, "w") as f:
        f.write(updated_content)

    print(f"Updated {INIT_FILE} to version {new_version}")


def update_badge():
    """Update the PyPI badge in README.md."""
    try:
        subprocess.run(["python3", "scripts/update_badge.py"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Failed to update the PyPI badge")


def main():
    """Bump the version and update all version references."""
    if len(sys.argv) != 2 or sys.argv[1] not in ["major", "minor", "patch"]:
        print("Usage: python bump_version.py [major|minor|patch]")
        sys.exit(1)

    bump_type = sys.argv[1]
    current_version = get_current_version()
    new_version = bump_version(current_version, bump_type)

    print(f"Bumping version from {current_version} to {new_version}")

    update_pyproject(new_version)
    update_init(new_version)
    update_badge()

    print(f"Version bumped to {new_version}")
    print("\nTo commit and push these changes:")
    print(f"  git add {PYPROJECT_FILE} {INIT_FILE} README.md")
    print(f'  git commit -m "Bump version to {new_version}"')
    print("  git push")


if __name__ == "__main__":
    main()

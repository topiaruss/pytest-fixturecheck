#!/usr/bin/env python
"""
Update the PyPI badge in README.md to the current version from pyproject.toml.
"""

import re
import sys
from pathlib import Path


def get_current_version():
    """Extract the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    with open(pyproject_path, "r") as f:
        content = f.read()

    # Find the version line
    version_match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not version_match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    return version_match.group(1)


def update_badge(version):
    """Update the PyPI badge in README.md to point to the specified version."""
    readme_path = Path("README.md")

    if not readme_path.exists():
        print("Error: README.md not found")
        sys.exit(1)

    with open(readme_path, "r") as f:
        lines = f.readlines()

    # Find the PyPI badge line
    badge_found = False
    for i, line in enumerate(lines):
        if (
            "PyPI version" in line
            and "https://pypi.org/project/pytest-fixturecheck/" in line
        ):
            # This is the line with the PyPI badge
            print(f"Found badge at line {i+1}: {line.strip()}")

            # Extract portions before and after version
            start_idx = line.find("https://pypi.org/project/pytest-fixturecheck/")
            if start_idx == -1:
                continue

            # Find closing parenthesis after the URL
            end_idx = line.find(")", start_idx)
            if end_idx == -1:
                continue

            before = line[:start_idx]
            after = line[end_idx:]

            # Replace with new version
            new_line = (
                before
                + f"https://pypi.org/project/pytest-fixturecheck/{version}/"
                + after
            )
            lines[i] = new_line
            badge_found = True
            break

    if not badge_found:
        print("Warning: Could not find PyPI badge in README.md")
        return False

    with open(readme_path, "w") as f:
        f.writelines(lines)

    return True


def main():
    """Update the PyPI badge in README.md to the current version."""
    version = get_current_version()
    print(f"Current version: {version}")

    if update_badge(version):
        print(f"Successfully updated PyPI badge in README.md to version {version}")
    else:
        print("Failed to update PyPI badge in README.md")


if __name__ == "__main__":
    main()

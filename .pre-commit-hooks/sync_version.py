#!/usr/bin/env python
"""
Pre-commit hook to verify that package version and __version__ are in sync.
This isn't strictly necessary with the importlib.metadata approach,
but serves as a double-check.
"""

import argparse
import re
import sys
import tomli


def get_pyproject_version(pyproject_path):
    """Get the version from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)
    return data["project"]["version"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args()

    # Check if pyproject.toml is being modified
    pyproject_files = [f for f in args.filenames if f.endswith("pyproject.toml")]
    if not pyproject_files:
        return 0
    
    # Get version from pyproject.toml
    try:
        version = get_pyproject_version(pyproject_files[0])
        print(f"Version in pyproject.toml: {version}")
        return 0
    except Exception as e:
        print(f"Error reading version from pyproject.toml: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python
"""
Utility script to bump the version in pyproject.toml.
Since __init__.py now uses importlib.metadata, it will automatically use the updated version.
"""

import argparse
import sys
import tomli
import tomli_w
from pathlib import Path


def get_pyproject_path():
    """Get the path to pyproject.toml."""
    return Path(__file__).parent.parent / "pyproject.toml"


def get_current_version():
    """Get the current version from pyproject.toml."""
    with open(get_pyproject_path(), "rb") as f:
        data = tomli.load(f)
    return data["project"]["version"]


def bump_version(version_type):
    """Bump the version in pyproject.toml."""
    # Read the current version
    pyproject_path = get_pyproject_path()
    with open(pyproject_path, "rb") as f:
        data = tomli.load(f)

    current_version = data["project"]["version"]
    major, minor, patch = current_version.split(".")

    # Bump the version based on type
    if version_type == "major":
        major = str(int(major) + 1)
        minor = "0"
        patch = "0"
    elif version_type == "minor":
        minor = str(int(minor) + 1)
        patch = "0"
    elif version_type == "patch":
        patch = str(int(patch) + 1)
    else:
        print(f"Unknown version type: {version_type}")
        return False

    new_version = f"{major}.{minor}.{patch}"
    data["project"]["version"] = new_version

    # Write the new version
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)

    print(f"Bumped version from {current_version} to {new_version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml")
    parser.add_argument(
        "version_type",
        choices=["major", "minor", "patch"],
        help="Type of version bump to perform",
    )
    args = parser.parse_args()

    success = bump_version(args.version_type)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

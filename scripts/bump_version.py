#!/usr/bin/env python
"""
Utility script to bump the version in pyproject.toml and update the CHANGELOG.md.
Since __init__.py now uses importlib.metadata, it will automatically use the updated version.
"""

import argparse
import sys
import tomli
import tomli_w
from pathlib import Path
from datetime import date
import re


def get_pyproject_path():
    """Get the path to pyproject.toml."""
    return Path(__file__).parent.parent / "pyproject.toml"


def get_changelog_path():
    """Get the path to CHANGELOG.md."""
    return Path(__file__).parent.parent / "CHANGELOG.md"


def get_current_version():
    """Get the current version from pyproject.toml."""
    with open(get_pyproject_path(), "rb") as f:
        data = tomli.load(f)
    return data["project"]["version"]


def update_changelog(new_version, version_type):
    """Update the CHANGELOG.md with the new version and today's date."""
    changelog_path = get_changelog_path()
    today = date.today().strftime("%Y-%m-%d")
    
    # Read the current changelog
    with open(changelog_path, "r") as f:
        content = f.read()
    
    # Check if there's already an entry for this version
    version_pattern = rf"## {re.escape(new_version)} \((.*?)\)"
    existing_version_match = re.search(version_pattern, content)
    
    if existing_version_match:
        # Update the date for the existing version entry
        updated_content = re.sub(
            rf"## {re.escape(new_version)} \((.*?)\)",
            f"## {new_version} ({today})",
            content
        )
        with open(changelog_path, "w") as f:
            f.write(updated_content)
        print(f"Updated date for existing version {new_version} to {today}")
        return True
    
    # Create a new entry template based on version type
    if version_type == "major":
        new_entry = f"\n## {new_version} ({today})\n\n### New Features\n- \n\n### Breaking Changes\n- \n"
    elif version_type == "minor":
        new_entry = f"\n## {new_version} ({today})\n\n### New Features\n- \n\n### Bug Fixes\n- \n"
    else:  # patch
        new_entry = f"\n## {new_version} ({today})\n\n### Bug Fixes\n- \n"
    
    # Insert the new entry after the "# Changelog" line
    changelog_pattern = r"# Changelog\n"
    if re.search(changelog_pattern, content):
        updated_content = re.sub(
            changelog_pattern,
            f"# Changelog{new_entry}",
            content,
            count=1
        )
        
        with open(changelog_path, "w") as f:
            f.write(updated_content)
        
        print(f"Updated CHANGELOG.md with new version {new_version} and date {today}")
        return True
    else:
        print("Could not find '# Changelog' heading in CHANGELOG.md")
        return False


def bump_version(version_type):
    """Bump the version in pyproject.toml and update the changelog."""
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

    # Write the new version to pyproject.toml
    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)

    print(f"Bumped version from {current_version} to {new_version}")
    
    # Update the changelog
    update_changelog(new_version, version_type)
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Bump version in pyproject.toml and update CHANGELOG.md")
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

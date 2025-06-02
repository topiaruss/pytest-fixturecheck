def test_is_excluded_path():
    """Test the is_excluded_path function with various path patterns."""
    from pathlib import Path

    from pytest_fixturecheck.utils import is_excluded_path

    # Test virtual environment patterns
    venv_paths = [
        Path(".venv/lib/python3.13/test.py"),
        Path("venv/test.py"),
        Path(".env/test.py"),
        Path("env/bin/test.py"),
        Path(".virtualenv/test.py"),
        Path("virtualenv/test.py"),
        Path(".pyenv/test.py"),
        Path("pyenv/test.py"),
    ]

    for path in venv_paths:
        assert is_excluded_path(path), f"Path {path} should be excluded"

    # Test package patterns
    package_paths = [
        Path("lib/python3.13/site-packages/test.py"),
        Path("node_modules/test.js"),
        Path("__pycache__/test.pyc"),
        Path(".tox/py313/test.py"),
        Path(".pytest_cache/test.py"),
        Path(".mypy_cache/test.py"),
        Path("build/lib/test.py"),
        Path("dist/test.py"),
        Path(".git/hooks/test.py"),
        Path("htmlcov/test.html"),
        Path("mypackage.egg-info/test.py"),
    ]

    for path in package_paths:
        assert is_excluded_path(path), f"Path {path} should be excluded"

    # Test legitimate paths that should NOT be excluded
    legitimate_paths = [
        Path("tests/test_example.py"),
        Path("test_module.py"),
        Path("src/mypackage/test_utils.py"),
        Path("conftest.py"),
        Path("my_test_file.py"),
        Path("unit/test_basic.py"),
        Path("integration/test_api.py"),
    ]

    for path in legitimate_paths:
        assert not is_excluded_path(path), f"Path {path} should NOT be excluded"

    # Test edge cases
    edge_cases = [
        (Path("test_env.py"), False),  # Contains "env" but not as directory
        (Path("envtest/test.py"), False),  # Starts with "env" but different
        (Path("testenv/test.py"), False),  # Ends with "env" but different
        (Path("some/deep/.venv/nested/test.py"), True),  # Nested .venv
        (Path("dist_packages/test.py"), False),  # Similar but not exact match
    ]

    for path, should_exclude in edge_cases:
        result = is_excluded_path(path)
        assert result == should_exclude, (
            f"Path {path} exclusion should be {should_exclude}, got {result}"
        )

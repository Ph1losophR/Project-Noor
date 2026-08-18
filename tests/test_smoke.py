"""Layout sanity: the module map of SSOT §4.1 exists and imports."""

import importlib
import sys


def test_the_interpreter_is_at_least_python_312():
    # Arrange / Act / Assert
    assert sys.version_info >= (3, 12)


def test_the_ssot_module_layout_exists_and_imports():
    # Arrange
    modules = ("noor", "noor.canon", "noor.engine", "noor.catalogue", "noor.app")

    # Act / Assert
    for name in modules:
        module = importlib.import_module(name)
        assert module.__doc__, f"{name} must carry a docstring stating its boundary role"

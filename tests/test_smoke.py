"""Layout sanity: the module map of SSOT §4.1 exists and imports."""

import importlib


def test_the_ssot_module_layout_exists_and_imports():
    # Arrange
    modules = ("noor", "noor.canon", "noor.engine", "noor.catalogue", "noor.app")

    # Act / Assert
    for name in modules:
        module = importlib.import_module(name)
        assert module.__doc__, f"{name} must carry a docstring stating its boundary role"

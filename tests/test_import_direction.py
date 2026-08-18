"""The device-boundary seam test (SSOT §4.2).

`app` imports from `canon`, `engine`, and `catalogue` — never the reverse.
`canon` and `engine` are pure: no database, no HTTP, no filesystem, no clock
(§8.4 invariant 8 applied to the whole boundary). `canon` additionally never
names a treatment threshold: §6.4's three boundary types are separate, and
`docs/testing-standards.md` requires a test that proves they are not read from
one another. This test exists from the first commit, before there is anything
to import (§14 step 1).
"""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src" / "noor"

BOUNDARY_PACKAGES = ("canon", "engine", "catalogue")
PURE_PACKAGES = ("canon", "engine")

FORBIDDEN_IMPORT_ROOTS_IN_PURE = frozenset(
    {
        "sqlalchemy",
        "psycopg",
        "psycopg2",
        "asyncpg",
        "fastapi",
        "starlette",
        "httpx",
        "requests",
        "aiohttp",
        "socket",
        "os",
        "pathlib",
        "shutil",
        "io",
        "time",
    }
)

# Attribute calls that read the wall clock. Time enters the boundary as data
# (§4.2): timestamps on captures, explicit arguments — never a `now()` call.
FORBIDDEN_CLOCK_CALLS_IN_PURE = frozenset(
    {"now", "utcnow", "today", "time", "monotonic", "perf_counter"}
)

# §6.4: a treatment threshold is never reused as a data-entry validator. `canon`
# validates data; thresholds are the engine's, from a compiled snapshot. Any
# identifier naming one inside canon means the two have been wired together.
FORBIDDEN_SUBSTRINGS_IN_CANON = ("threshold", "target_range")


def _python_files(package: str) -> list[Path]:
    directory = SRC / package
    if not directory.exists():
        return []
    return sorted(directory.rglob("*.py"))


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    package_parts = ("noor", *path.relative_to(SRC).parts[:-1])
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base_parts = package_parts[: len(package_parts) - node.level + 1] if node.level else ()
            if node.module is not None:
                module = ".".join((*base_parts, *node.module.split(".")))
                modules.append(module)
                if not node.level and node.module == "noor":
                    modules.extend(f"{module}.{alias.name}" for alias in node.names)
            else:
                modules.extend(".".join((*base_parts, alias.name)) for alias in node.names)
    return modules


def _called_attributes(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]


def _identifiers(path: Path) -> list[str]:
    """Every name the code *uses* — not comments or docstrings, which may say
    "threshold" while explaining why there isn't one."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.extend(alias.name for alias in node.names)
    return names


@pytest.mark.parametrize("package", BOUNDARY_PACKAGES)
def test_boundary_packages_never_import_app(package: str):
    # Arrange / Act
    offenders = [
        (path, module)
        for path in _python_files(package)
        for module in _imported_modules(path)
        if module == "noor.app" or module.startswith("noor.app.")
    ]

    # Assert
    assert not offenders, f"{package} must never import app (SSOT §4.2): {offenders}"


@pytest.mark.parametrize("package", PURE_PACKAGES)
def test_pure_packages_import_no_io_or_clock_modules(package: str):
    # Arrange / Act
    offenders = [
        (path, module)
        for path in _python_files(package)
        for module in _imported_modules(path)
        if module.split(".")[0] in FORBIDDEN_IMPORT_ROOTS_IN_PURE
    ]

    # Assert
    assert not offenders, (
        f"pure package {package} must not import I/O or clock modules "
        f"(SSOT §4.2, §8.4.8): {offenders}"
    )


@pytest.mark.parametrize("package", PURE_PACKAGES)
def test_pure_packages_never_read_the_wall_clock(package: str):
    # Arrange / Act
    offenders = [
        (path, attribute)
        for path in _python_files(package)
        for attribute in set(_called_attributes(path)) & FORBIDDEN_CLOCK_CALLS_IN_PURE
    ]

    # Assert
    assert not offenders, (
        f"pure package {package} reads the wall clock; time enters as data (SSOT §4.2): {offenders}"
    )


def test_canon_never_names_a_treatment_threshold():
    # Arrange / Act — §6.4: the three boundary types are separate, and the
    # testing standards require a test that they are not read from one another.
    # canon's envelopes are data-validity bounds; a threshold here would mean a
    # clinical decision boundary had leaked into data entry.
    offenders = [
        (path, name)
        for path in _python_files("canon")
        for name in _identifiers(path)
        if any(substring in name.lower() for substring in FORBIDDEN_SUBSTRINGS_IN_CANON)
    ]

    # Assert
    assert not offenders, f"canon must never read a treatment threshold (SSOT §6.4): {offenders}"

import ast
from pathlib import Path

DOMAIN = Path(__file__).resolve().parents[1] / "src" / "noor" / "domain"
FORBIDDEN = ("noor.store", "noor.emr", "noor.web", "noor.content",
             "noor.serial", "noor.dispatch",
             "sqlite3", "starlette", "jinja2", "httpx", "uvicorn")
WALL_CLOCK = ("datetime.now(", "datetime.utcnow(", "date.today(", "time.time(")


def _imported_names(source: str) -> list[str]:
    names = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append(node.module or "")
    return names


def test_the_domain_imports_nothing_outside_itself():
    # Arrange
    modules = sorted(DOMAIN.glob("*.py"))
    assert modules, "the domain package has no modules to check"

    # Act
    offences = [
        (path.name, name)
        for path in modules
        for name in _imported_names(path.read_text(encoding="utf-8"))
        if name.startswith(FORBIDDEN)
    ]

    # Assert
    assert offences == []


def test_no_domain_module_reads_the_wall_clock():
    # Arrange
    modules = sorted(DOMAIN.glob("*.py"))

    # Act
    offences = [
        (path.name, read)
        for path in modules
        for read in WALL_CLOCK
        if read in path.read_text(encoding="utf-8")
    ]

    # Assert
    assert offences == []

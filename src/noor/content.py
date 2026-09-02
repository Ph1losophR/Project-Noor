"""Versioned clinical content (ADR 0007). Fails loudly; never half-loads."""
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONTENT_ROOT = Path(__file__).resolve().parents[2] / "docs" / "clinical-content"
REQUIRED_META = frozenset({"version", "dated", "source", "owner", "review_date"})
SUBJECTS = (
    "interval-events", "reason-lists", "response-windows", "drug-list",
    "physical-examination-elements", "vitals-by-condition", "self-care-items",
    "surveillance-intervals",
)
_BLOCK = re.compile(r"^```toml\n(.*?)^```", re.MULTILINE | re.DOTALL)


class ContentError(RuntimeError):
    """A content file is missing, malformed, or incomplete (ADR 0007)."""


@dataclass(frozen=True)
class Content:
    subject: str
    meta: dict
    data: dict


def load(subject: str, root: Path | None = None) -> Content:
    path = (root or CONTENT_ROOT) / f"{subject}.md"
    if not path.is_file():
        raise ContentError(f"no clinical content for {subject!r} at {path}")
    found = _BLOCK.search(path.read_text(encoding="utf-8"))
    if found is None:
        raise ContentError(f"{path.name} has no toml block")
    try:
        parsed = tomllib.loads(found.group(1))
    except tomllib.TOMLDecodeError as exc:
        raise ContentError(f"{path.name} is not valid toml: {exc}") from exc
    meta = parsed.pop("meta", {})
    missing = sorted(REQUIRED_META - set(meta))
    if missing:
        raise ContentError(f"{path.name} [meta] is missing {', '.join(missing)}")
    unknown = sorted(set(meta) - REQUIRED_META)
    if unknown:
        raise ContentError(f"{path.name} [meta] has unknown field {', '.join(unknown)}")
    return Content(subject, meta, parsed)


def all_subjects(root: Path | None = None) -> list[Content]:
    """Every shipped subject, loaded. Raises on the first one that will not."""
    return [load(subject, root=root) for subject in SUBJECTS]


def unowned_subjects(root: Path | None = None) -> list[str]:
    """Subjects whose owner is still 'Unassigned'. N8 wants this empty at ship."""
    directory = root or CONTENT_ROOT
    names = sorted(p.stem for p in directory.glob("*.md"))
    return [n for n in names if load(n, root=directory).meta["owner"] == "Unassigned"]

import pytest

from noor import content

BLOCK = """# Subject

| N8 field | Value |
|---|---|
| Version | 0.1 |

```toml
[meta]
version = "0.1"
dated = "2026-08-28"
source = "Clinical judgement"
owner = "Unassigned"
review_date = "Unset"

[rows]
items = ["one", "two"]
```
"""


def _write(root, name, text):
    (root / f"{name}.md").write_text(text, encoding="utf-8")


def test_a_subject_loads_its_n8_metadata_and_its_data(tmp_path):
    # Arrange
    _write(tmp_path, "subject", BLOCK)

    # Act
    loaded = content.load("subject", root=tmp_path)

    # Assert
    assert loaded.meta["version"] == "0.1"
    assert loaded.data["rows"]["items"] == ["one", "two"]


def test_a_missing_content_file_names_the_subject_it_could_not_find(tmp_path):
    # Act / Assert
    with pytest.raises(content.ContentError, match="surveillance-intervals"):
        content.load("surveillance-intervals", root=tmp_path)


def test_a_file_with_no_toml_block_is_refused(tmp_path):
    # Arrange
    _write(tmp_path, "prose-only", "# Prose only\n\nNo machine-readable block.\n")

    # Act / Assert
    with pytest.raises(content.ContentError, match="no toml block"):
        content.load("prose-only", root=tmp_path)


def test_malformed_toml_names_the_file_it_could_not_parse(tmp_path):
    # Arrange
    _write(tmp_path, "broken", "```toml\n[meta\nversion = 1\n```\n")

    # Act / Assert
    with pytest.raises(content.ContentError, match="broken"):
        content.load("broken", root=tmp_path)


def test_a_block_missing_an_n8_field_names_the_field(tmp_path):
    # Arrange
    _write(tmp_path, "unversioned",
           '```toml\n[meta]\nversion = "0.1"\ndated = "2026-08-28"\n'
           'source = "x"\nowner = "Someone"\n```\n')

    # Act / Assert
    with pytest.raises(content.ContentError, match="review_date"):
        content.load("unversioned", root=tmp_path)


def test_unowned_subjects_reports_every_file_still_waiting_for_an_owner(tmp_path):
    # Arrange
    _write(tmp_path, "waiting", BLOCK)
    _write(tmp_path, "owned", BLOCK.replace('"Unassigned"', '"Dr Somebody"'))

    # Act
    waiting = content.unowned_subjects(root=tmp_path)

    # Assert
    assert waiting == ["waiting"]


def test_every_shipped_content_file_loads():
    # Act
    subjects = content.all_subjects()

    # Assert — eight subjects, each parsing and each carrying all five N8 fields
    assert len(subjects) == 8
    assert all(set(s.meta) >= content.REQUIRED_META for s in subjects)


def test_a_meta_block_carrying_an_unknown_field_is_refused(tmp_path):
    # Arrange
    _write(tmp_path, "over-specified",
           '```toml\n[meta]\nversion = "0.1"\ndated = "2026-08-28"\n'
           'source = "x"\nowner = "Someone"\nreview_date = "Unset"\n'
           'reviewer = "Dr Someone"\n```\n')

    # Act / Assert
    with pytest.raises(content.ContentError, match="reviewer"):
        content.load("over-specified", root=tmp_path)

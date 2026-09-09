"""Design system §12.1's admitted scope, read as text. There is no Python here to cover:
§14 already names the autosave as sitting outside the test gate, so what this file checks
is that the script stayed inside its scope — not that it works."""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "src" / "noor" / "web"
SCRIPT = WEB / "static" / "noor.js"
TEMPLATES = WEB / "templates"

# §12.1's three prohibitions, as the words that would appear if one were broken.
FORBIDDEN = ("innerHTML", "location", "history.", "createElement", "insertAdjacent")


def test_the_one_admitted_script_exists_and_is_one_file():
    # Arrange / Act
    files = sorted(p.name for p in (WEB / "static").glob("*.js"))

    # Assert — §12: one script file, and §12.1 is the whole of what may live in it.
    assert files == ["noor.js"]


def test_the_script_neither_routes_nor_renders():
    # Arrange
    text = SCRIPT.read_text(encoding="utf-8")

    # Act
    hits = [word for word in FORBIDDEN if word in text]

    # Assert — §12.1: no routing, no rendering, no clinical logic.
    assert hits == []


def test_the_script_posts_to_the_form_it_found_and_never_to_an_address_of_its_own():
    """§12.1: 'It posts to the same route the form posts to.' A URL written into the
    script would be a second copy of web_plan §2's address table."""
    # Arrange
    text = SCRIPT.read_text(encoding="utf-8")

    # Assert
    assert "form.action" in text
    assert "/visits/" not in text


def test_only_the_single_submit_sections_carry_the_autosave_attribute():
    """Medication Reconciliation is deliberately absent: its form carries an `act`, and a
    post on change would add a box every time a field lost focus."""
    # Arrange
    carrying = sorted(page.name for page in TEMPLATES.glob("*.html")
                      if "data-autosave" in page.read_text(encoding="utf-8"))

    # Assert
    assert carrying == ["section_care_plan.html", "section_concerns.html",
                        "section_examination.html", "section_free_text.html",
                        "section_self_care.html", "section_vitals.html"]


def test_the_reason_form_never_autosaves():
    """§5.10's reason path resolves the section. Posting it on change would resolve a
    section the moment a reason was highlighted, before anyone chose it."""
    # Arrange
    guard = (TEMPLATES / "section_base.html").read_text(encoding="utf-8")

    # Act
    before = guard.index("<script")

    # Assert — the attribute appears in no form on the shared page, reason form included.
    assert "data-autosave" not in guard[:before]

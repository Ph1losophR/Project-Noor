"""Design system §13's lint: the delivered files, read as text, failing on any value
that bypassed the token layer. Stdlib `re` and `pathlib` only, as §13 requires."""
import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "src" / "noor" / "web"
CSS = WEB / "static" / "noor.css"
PRINT_CSS = WEB / "static" / "print.css"
SCRIPT = WEB / "static" / "noor.js"
TEMPLATES = WEB / "templates"

PALETTE_END = "/* end palette */"
HEX = re.compile(r"#[0-9a-fA-F]{3,8}\b")
ROOT_BLOCK = re.compile(r":root[^{]*\{[^{}]*\}")
# §13's set: a hex, a px font-size, a border-radius or a padding value. `gap` rides
# the same space scale (§6), so it is linted with the padding family.
TOKENISED = re.compile(
    r"\b(font-size|border-radius|padding|padding-top|padding-right|padding-bottom"
    r"|padding-left|gap)\s*:\s*([^;{}]+)")
# A template that decides is a branch coverage cannot see (CLAUDE.md).
BRANCHING = re.compile(r"\{%-?\s*(?:if|elif|else)\b|\{\{[^}]*\sif\s|\|\s*default\s*\(")
FORBIDDEN = ("urgency", "severity", "priority", "acuity", "criticality")


def templates() -> list[Path]:
    return sorted(TEMPLATES.glob("*.html"))


def declarations(css: str, marker: str) -> dict[str, str]:
    """The `--name: value` pairs between one `/* … */` marker and the next. No comment
    appears inside a role block, which is what makes the next `/*` the region's end."""
    start = css.index(marker) + len(marker)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", css[start:css.index("/*", start)]))


def test_the_palette_marker_that_bounds_every_hex_is_present():
    # Arrange / Act
    css = CSS.read_text(encoding="utf-8")

    # Assert — without it the hex test below would pass by finding nothing to check.
    assert css.count(PALETTE_END) == 1


def test_no_hex_appears_below_the_palette_marker():
    # Arrange
    css = CSS.read_text(encoding="utf-8")

    # Act
    below = css.split(PALETTE_END)[1]

    # Assert
    assert HEX.findall(below) == []


def test_the_print_stylesheet_declares_no_colour_of_its_own():
    # Arrange / Act
    css = PRINT_CSS.read_text(encoding="utf-8")

    # Assert — §10 forces light by re-pointing the roles at the light palette, never
    # by restating a value.
    assert HEX.findall(css) == []


def test_size_and_space_outside_root_go_through_a_token():
    # Arrange
    css = ROOT_BLOCK.sub("", CSS.read_text(encoding="utf-8"))

    # Act
    loose = [f"{prop}: {value.strip()}" for prop, value in TOKENISED.findall(css)
             if "var(--" not in value and value.strip() != "0"]

    # Assert
    assert loose == []


def test_the_two_dark_role_blocks_declare_the_same_pairs():
    # Arrange
    css = CSS.read_text(encoding="utf-8")

    # Act
    preference = declarations(css, "/* roles: dark, under the OS preference */")
    toggle = declarations(css, "/* roles: dark, under the toggle */")

    # Assert — §9 wants both scopes; nothing but this stops them drifting apart.
    assert preference == toggle
    assert len(toggle) == 18


def test_the_two_light_role_blocks_declare_the_same_pairs():
    # Arrange
    css = CSS.read_text(encoding="utf-8")

    # Act
    default = declarations(css, "/* roles: light */")
    toggle = declarations(css, "/* roles: light, under the toggle */")

    # Assert
    assert default == toggle
    assert len(toggle) == 18


def test_no_template_decides_anything():
    # Arrange
    found = {}

    # Act
    for page in templates():
        hits = BRANCHING.findall(page.read_text(encoding="utf-8"))
        if hits:
            found[page.name] = hits

    # Assert
    assert found == {}


def test_no_template_reaches_past_the_roles_into_the_palette():
    # Arrange
    reaching = []

    # Act
    for page in templates():
        text = page.read_text(encoding="utf-8")
        if "--l-" in text or "--d-" in text:
            reaching.append(page.name)

    # Assert
    assert reaching == []


def test_no_screen_holds_two_subject_containers():
    # Arrange
    doubled = {}

    # Act
    for page in templates():
        count = page.read_text(encoding="utf-8").count('"subject')
        if count > 1:
            doubled[page.name] = count

    # Assert — §6: 'Two 24px containers on one screen is a defect.'
    assert doubled == {}


def test_the_words_context_md_forbids_appear_on_no_surface():
    # Arrange
    surfaces = [*templates(), CSS, PRINT_CSS, SCRIPT]
    found = {}

    # Act
    for surface in surfaces:
        text = surface.read_text(encoding="utf-8").lower()
        hits = [word for word in FORBIDDEN if word in text]
        if hits:
            found[surface.name] = hits

    # Assert — the ordering word is Escalation Tier and CONTEXT.md forbids the synonyms.
    assert found == {}


def test_the_script_declares_no_value_of_its_own():
    # Arrange / Act
    text = SCRIPT.read_text(encoding="utf-8")

    # Assert — §13's set, on §12's third delivered file. A colour or a size in the script
    # would be a style decision in the one place the token layer cannot reach.
    assert HEX.findall(text) == []
    assert TOKENISED.findall(text) == []

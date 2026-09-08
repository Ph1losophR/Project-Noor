"""The four faces design system §12 names, present and self-hosted."""
from pathlib import Path

STATIC = Path(__file__).resolve().parents[2] / "src" / "noor" / "web" / "static"
FONTS = ("EBGaramond-Medium.woff2", "DMSans-Regular.woff2",
         "DMSans-SemiBold.woff2", "NotoNaskhArabic-Regular.woff2")


def test_every_face_the_design_system_names_is_on_disk():
    # Arrange
    directory = STATIC / "fonts"

    # Act
    missing = [name for name in FONTS if not (directory / name).is_file()]

    # Assert
    assert missing == []


def test_every_face_is_a_real_woff2_and_not_an_error_page():
    # Arrange
    directory = STATIC / "fonts"

    # Act
    heads = {name: (directory / name).read_bytes()[:4] for name in FONTS}
    sizes = {name: (directory / name).stat().st_size for name in FONTS}

    # Assert
    assert set(heads.values()) == {b"wOF2"}
    assert min(sizes.values()) > 5_000


def test_the_licence_the_open_font_license_requires_travels_with_them():
    # Arrange
    licence = STATIC / "fonts" / "LICENSES.md"

    # Act
    text = licence.read_text(encoding="utf-8")

    # Assert
    assert "SIL Open Font License" in text
    for name in FONTS:
        assert name in text


def test_the_stylesheet_names_exactly_the_faces_on_disk():
    # Arrange
    import re
    css = (STATIC / "noor.css").read_text(encoding="utf-8")

    # Act
    named = set(re.findall(r'url\("fonts/([^"]+)"\)', css))

    # Assert — a face on disk that nothing loads is dead weight; a face loaded that
    # is not on disk is invisible text, because §12 sets font-display: block.
    assert named == set(FONTS)

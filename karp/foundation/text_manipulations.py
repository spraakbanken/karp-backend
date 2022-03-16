import unicodedata


def shave_marks(txt: str) -> str:
    """Remove all diacritic marks."""
    norm_txt = unicodedata.normalize("NFD", txt)
    shaved = "".join(c for c in norm_txt if not unicodedata.combining(c))
    return unicodedata.normalize("NFC", shaved)

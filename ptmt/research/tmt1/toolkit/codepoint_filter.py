import unicodedata

_illegal_codepoints = ("P", "S", "Z", "C", "M")


def is_illegal_char(word: str) -> bool:
    """Filter for illegal codepoints"""
    if len(word) == 1:
        category = unicodedata.category(word)
        return category[0] in _illegal_codepoints
    return False

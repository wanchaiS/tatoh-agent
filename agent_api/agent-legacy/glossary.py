"""Glossary-based i18n for UI text."""

GLOSSARY: dict[str, dict[str, str]] = {
    "confirm_criteria": {"th": "ถูกต้อง", "en": "Correct"},
    "update_criteria": {"th": "แก้ไขการค้นหา", "en": "Change criteria"},
}


def t(key: str, lang: str) -> str:
    """Look up a translated string. Non-Thai languages default to English."""
    entry = GLOSSARY.get(key, {})
    lookup_lang = lang if lang == "th" else "en"
    return entry.get(lookup_lang, entry.get("en", key))

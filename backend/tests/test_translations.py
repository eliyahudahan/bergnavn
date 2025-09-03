# tests/test_translations.py
import pytest
from backend.utils.translations import translate


def test_translate_existing_key_en():
    assert translate("dashboard", "en", "global") == "Dashboard"


def test_translate_existing_key_no():
    assert translate("dashboard", "no", "global") == "Dashbord"


def test_translate_fallback_to_en():
    # Key does not exist in Norwegian, should fall back to English
    assert translate("nonexistent_key", "no", "global") == "nonexistent_key"


def test_translate_default_lang():
    # If no language is provided, English should be used by default
    assert translate("dashboard", section="global") == "Dashboard"

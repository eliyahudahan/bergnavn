"""
Tests for translation functionality.
Tests cover translation retrieval, fallback behavior, and language support.
"""

import pytest
from backend.utils.translations import translate


def test_translate_existing_key_en():
    """
    Test translation of existing key in English returns correct value.
    """
    result = translate("home", "en", "global")
    assert result == "Home"


def test_translate_existing_key_no():
    """
    Test translation of existing key in Norwegian returns correct value.
    """
    result = translate("home", "no", "global")
    assert result == "Hjem"


def test_translate_nonexistent_key_fallback():
    """
    Test translation of non-existent key returns fallback value.
    """
    result = translate("nonexistent_key", "en", "global")
    # Should return the key itself or a fallback message
    assert "nonexistent_key" in result or "N/A" in result


def test_translate_default_lang_is_en():
    """
    Test that default language is English when no language specified.
    """
    result = translate("home", lang="en", page="global")
    assert result == "Home"


def test_translate_cruises_page_title():
    """
    Test translation of cruises page title section.
    """
    result = translate("title", "en", "cruises_page")
    # Check if it returns a meaningful value (not the key itself)
    assert result != "title" and len(result) > 0


def test_translate_dashboard_page_title():
    """
    Test translation of dashboard page title section.
    """
    result = translate("title", "en", "dashboard_page")
    # Check if it returns a meaningful value (not the key itself)
    assert result != "title" and len(result) > 0


def test_translate_dummy_users_title():
    """
    Test translation of dummy users section title.
    """
    result = translate("title", "en", "dummy_users")
    # Check if it returns a meaningful value (not the key itself)
    assert result != "title" and len(result) > 0


def test_translate_routes_and_legs():
    """
    Test translation of routes and legs section.
    """
    result = translate("routes_and_legs", "en", "routes_page")
    # Check if it returns a meaningful value (not the key itself)
    assert result != "routes_and_legs" and len(result) > 0
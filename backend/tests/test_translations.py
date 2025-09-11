# tests/test_translations.py
import pytest
from backend.utils.translations import translate

# --- Global section tests ---
def test_translate_existing_key_en():
    assert translate("dashboard", "en", "global") == "Dashboard"

def test_translate_existing_key_no():
    assert translate("dashboard", "no", "global") == "Dashbord"

def test_translate_nonexistent_key_fallback():
    # Key does not exist, should return the key itself
    assert translate("nonexistent_key", "no", "global") == "nonexistent_key"

def test_translate_default_lang_is_en():
    assert translate("dashboard", section="global") == "Dashboard"


# --- Cruises page tests ---
def test_translate_cruises_page_title():
    assert translate("title", "en", "cruises_page") == "Available Cruises"
    assert translate("title", "no", "cruises_page") == "Tilgjengelige cruise"


# --- Dashboard page tests ---
def test_translate_dashboard_page_title():
    assert translate("title", "en", "dashboard_page") == "🛳️ Voyage Dashboard"
    assert translate("title", "no", "dashboard_page") == "🛳️ Reisedashbord"


# --- Dummy users tests ---
def test_translate_dummy_users_title():
    assert translate("title", "en", "dummy_users") == "Dummy Users"
    assert translate("title", "no", "dummy_users") == "Dummybrukere"


# --- Routes page tests (critical fix for your issue) ---
def test_translate_routes_and_legs():
    # Verify correct translation for both languages
    assert translate("routes_and_legs", "en", "routes_page") == "Routes and Legs"
    assert translate("routes_and_legs", "no", "routes_page") == "Ruter og etapper"

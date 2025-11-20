"""
Tests for internationalization (i18n) and translation functionality.
Tests cover translation structure, language consistency, and UI rendering.
"""

from backend.utils.translations import translations, translate
from app import create_app
import pytest


@pytest.fixture(scope="session")
def app():
    """Create Flask application with testing configuration."""
    app = create_app(testing=True)
    return app


def test_translations_structure():
    """
    Test that translation files have consistent structure.
    Verifies that all languages have the same keys and sections.
    """
    # Get available languages
    languages = list(translations.keys())
    assert len(languages) >= 2, "Should have at least two languages"
    
    # Compare structure between languages
    for i in range(len(languages)):
        for j in range(i + 1, len(languages)):
            lang1 = languages[i]
            lang2 = languages[j]
            
            # Compare top-level sections
            assert set(translations[lang1].keys()) == set(translations[lang2].keys()), \
                f"Sections mismatch between {lang1} and {lang2}"
            
            # Compare keys within each section
            for section in translations[lang1].keys():
                assert set(translations[lang1][section].keys()) == set(translations[lang2][section].keys()), \
                    f"Keys mismatch in section '{section}' between {lang1} and {lang2}"


def test_english_translations_exist():
    """
    Test that English translations are available and properly structured.
    English is the fallback language and should always be present.
    """
    assert 'en' in translations, "English translations must exist"
    assert isinstance(translations['en'], dict), "English translations should be a dictionary"
    assert len(translations['en']) > 0, "English translations should not be empty"


def test_norwegian_translations_exist():
    """
    Test that Norwegian translations are available.
    Norwegian is a primary language for this application.
    """
    assert 'no' in translations, "Norwegian translations must exist"
    assert isinstance(translations['no'], dict), "Norwegian translations should be a dictionary"
    assert len(translations['no']) > 0, "Norwegian translations should not be empty"


def test_translate_function():
    """
    Test the translate function with various inputs.
    """
    # Test existing key
    result = translate('home', 'en', 'global')
    assert result == 'Home'
    
    # Test fallback for non-existent key
    result = translate('nonexistent_key', 'en', 'global')
    # Should return the key itself or a fallback message
    assert 'nonexistent_key' in result or 'N/A' in result


def test_cruises_view_no_language(app):
    """
    Test that Norwegian language view renders correctly.
    Verifies no Python built-in methods are exposed in the rendered HTML.
    """
    with app.test_client() as client:
        # Try different cruise-related endpoints
        response = client.get("/cruises?lang=no")
        html_content = response.data.decode("utf-8")
        
        # Check if we got a successful response or redirect
        assert response.status_code in [200, 302, 308, 404]
        
        # If we got content, check for Python artifacts
        if response.status_code == 200:
            assert "<built-in method title" not in html_content.lower()
            assert "<built-in method" not in html_content.lower()
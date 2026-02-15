"""
Flask integration for dynamic translation system.
Provides template helpers and API endpoints for i18n support.
"""
from flask import request, current_app
from datetime import datetime  
import json
import os
from functools import lru_cache
from typing import Dict, Any, Optional
import logging

# Configure logger
logger = logging.getLogger(__name__)

class DynamicTranslator:
    """
    Dynamic translation system for Flask templates.
    Loads translations on-demand and caches them for performance.
    """
    
    def __init__(self, translations_dir: str = "backend/translations/data"):
        """
        Initialize the dynamic translator.
        
        Args:
            translations_dir: Directory containing translation JSON files
        """
        self.translations_dir = translations_dir
        
        # Validate translations directory exists
        if not os.path.exists(translations_dir):
            logger.warning(f"Translations directory not found: {translations_dir}")
            os.makedirs(translations_dir, exist_ok=True)
    
    @lru_cache(maxsize=2)
    def _load_language(self, lang: str) -> Dict[str, Dict[str, str]]:
        """
        Load translations for a language (cached).
        
        Args:
            lang: Language code ('en' or 'no')
            
        Returns:
            Dictionary of translations for the language
        """
        filepath = os.path.join(self.translations_dir, f"{lang}.json")
        
        if not os.path.exists(filepath):
            logger.debug(f"Translation file not found: {filepath}")
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data)} categories for language: {lang}")
                return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filepath}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load translations for {lang}: {e}")
            return {}
    
    def translate(self, key: str, lang: str = 'en', 
                 default: Optional[str] = None) -> str:
        """
        Translate a key to the specified language.
        
        Args:
            key: Translation key (format: "category.key" or just "key")
            lang: Language code ('en' or 'no')
            default: Default value if translation not found
            
        Returns:
            Translated string or default/key if not found
        """
        # Validate language
        if lang not in ['en', 'no']:
            logger.warning(f"Unsupported language: {lang}, falling back to 'en'")
            lang = 'en'
        
        # Load translations for language
        translations = self._load_language(lang)
        
        # Split key into category and subkey
        if '.' in key:
            category, subkey = key.split('.', 1)
        else:
            category = 'global'
            subkey = key
        
        # Look up translation
        category_dict = translations.get(category, {})
        translated = category_dict.get(subkey)
        
        if translated:
            return translated
        
        # Not found - try English as fallback for Norwegian
        if lang == 'no':
            english_translation = self.translate(key, 'en', default)
            if english_translation and english_translation != key:
                # Return English text (better than key)
                return f"[NO TRANSLATION] {english_translation}"
        
        # Return default or key
        if default is not None:
            return default
        return key
    
    def get_all(self, lang: str = 'en') -> Dict[str, Any]:
        """
        Get all translations for a language.
        
        Args:
            lang: Language code ('en' or 'no')
            
        Returns:
            Dictionary of all translations for the language
        """
        # Validate language
        if lang not in ['en', 'no']:
            lang = 'en'
        
        translations = self._load_language(lang)
        
        # Flatten for easier template access
        flattened = {}
        for category, items in translations.items():
            for key, value in items.items():
                flattened[f"{category}.{key}"] = value
        
        return flattened
    
    def get_categories(self, lang: str = 'en') -> Dict[str, Dict[str, str]]:
        """
        Get translations grouped by category.
        
        Args:
            lang: Language code
            
        Returns:
            Dictionary with categories as keys
        """
        return self._load_language(lang)
    
    def has_translation(self, key: str, lang: str = 'en') -> bool:
        """
        Check if a translation exists for a key.
        
        Args:
            key: Translation key
            lang: Language code
            
        Returns:
            True if translation exists
        """
        if '.' in key:
            category, subkey = key.split('.', 1)
        else:
            category = 'global'
            subkey = key
        
        translations = self._load_language(lang)
        category_dict = translations.get(category, {})
        
        return subkey in category_dict
    
    def clear_cache(self):
        """Clear the language cache."""
        self._load_language.cache_clear()
        logger.info("Translation cache cleared")
    
    def cache_info(self):
        """Get cache information."""
        return self._load_language.cache_info()

# Global translator instance
_translator: Optional[DynamicTranslator] = None

def get_translator() -> DynamicTranslator:
    """
    Get or create the global translator instance.
    
    Returns:
        DynamicTranslator instance
    """
    global _translator
    if _translator is None:
        _translator = DynamicTranslator()
    return _translator

def init_app(app):
    """
    Initialize translation system with Flask app.
    
    Args:
        app: Flask application instance
    """
    from flask import jsonify
    
    @app.context_processor
    def inject_translations():
        """
        Inject translations into all templates.
        This makes the 't' function available in every template.
        """
        # Get language from URL parameter or default to English
        lang = 'en'
        
        # Try to get language from URL parameters
        if request.view_args:
            lang = request.view_args.get('lang', 'en')
        elif request.args:
            lang = request.args.get('lang', 'en')
        
        # Ensure valid language code
        if lang not in ['en', 'no']:
            lang = 'en'
        
        translator = get_translator()
        
        def t(key: str, category: str = 'global', 
              default: Optional[str] = None) -> str:
            """
            Translation helper for templates.
            
            Args:
                key: Translation key
                category: Category for the key (default: 'global')
                default: Default text if translation not found
                
            Returns:
                Translated text
            """
            full_key = f"{category}.{key}" if category != 'global' else key
            result = translator.translate(full_key, lang, default or key)
            return result
        
        def t_all() -> Dict[str, str]:
            """
            Get all translations for current language.
            
            Returns:
                Dictionary of all translations
            """
            return translator.get_all(lang)
        
        def get_language() -> str:
            """Get current language code."""
            return lang
        
        def is_english() -> bool:
            """Check if current language is English."""
            return lang == 'en'
        
        def is_norwegian() -> bool:
            """Check if current language is Norwegian."""
            return lang == 'no'
        
        def translate_many(keys: list, category: str = 'global') -> Dict[str, str]:
            """Translate multiple keys at once."""
            results = {}
            for key in keys:
                results[key] = t(key, category)
            return results
        
        return {
            'lang': lang,
            't': t,
            't_all': t_all,
            'get_language': get_language,
            'is_english': is_english,
            'is_norwegian': is_norwegian,
            'translate_many': translate_many,
            'translations': t_all()  # For direct access if needed
        }
    
    # Add translation API endpoints
    @app.route('/api/translations/<lang>', methods=['GET'])
    def get_translations_api(lang: str):
        """
        API endpoint to get translations for a language.
        
        Args:
            lang: Language code ('en' or 'no')
            
        Returns:
            JSON response with translations
        """
        translator = get_translator()
        
        # Validate language
        if lang not in ['en', 'no']:
            return jsonify({
                'error': f'Unsupported language: {lang}',
                'supported_languages': ['en', 'no']
            }), 400
        
        translations = translator.get_all(lang)
        
        return jsonify({
            'language': lang,
            'translations': translations,
            'count': len(translations)
        })
    
    @app.route('/api/translations/categories/<lang>', methods=['GET'])
    def get_translation_categories(lang: str):
        """
        API endpoint to get translations grouped by category.
        
        Args:
            lang: Language code
            
        Returns:
            JSON response with categorized translations
        """
        translator = get_translator()
        
        if lang not in ['en', 'no']:
            return jsonify({'error': 'Unsupported language'}), 400
        
        categories = translator.get_categories(lang)
        
        return jsonify({
            'language': lang,
            'categories': categories,
            'category_count': len(categories)
        })
    
    @app.route('/api/translations/refresh', methods=['POST'])
    def refresh_translations():
        """
        Refresh translations cache.
        Useful after updating translation files.
        
        Returns:
            JSON response with status
        """
        translator = get_translator()
        translator.clear_cache()
        
        return jsonify({
            'status': 'success',
            'message': 'Translation cache cleared',
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/translations/health', methods=['GET'])
    def translation_health():
        """
        Health check endpoint for translation system.
        
        Returns:
            JSON response with system status
        """
        translator = get_translator()
        
        # Check if translation files exist
        en_exists = os.path.exists(os.path.join(translator.translations_dir, 'en.json'))
        no_exists = os.path.exists(os.path.join(translator.translations_dir, 'no.json'))
        
        # Load a sample translation to test functionality
        test_key = 'global.home'
        en_translation = translator.translate(test_key, 'en', 'not_found')
        no_translation = translator.translate(test_key, 'no', 'not_found')
        
        # Get cache info
        try:
            cache_info = translator.cache_info()
            cache_size = cache_info.currsize
            cache_hits = cache_info.hits
            cache_misses = cache_info.misses
        except:
            cache_size = 0
            cache_hits = 0
            cache_misses = 0
        
        status = 'healthy' if en_exists else 'degraded'
        
        return jsonify({
            'status': status,
            'english_file': en_exists,
            'norwegian_file': no_exists,
            'cache_info': {
                'size': cache_size,
                'hits': cache_hits,
                'misses': cache_misses
            },
            'sample_translation': {
                'key': test_key,
                'english': en_translation,
                'norwegian': no_translation
            },
            'supported_languages': ['en', 'no'],
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/translations/translate', methods=['GET'])
    def translate_text():
        """
        API endpoint to translate specific text.
        
        Query params:
            text: Text to translate
            lang: Target language (default: 'en')
            category: Category (default: 'global')
        """
        text = request.args.get('text', '')
        lang = request.args.get('lang', 'en')
        category = request.args.get('category', 'global')
        
        if not text:
            return jsonify({'error': 'Missing text parameter'}), 400
        
        translator = get_translator()
        
        # Create a key from the text
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        key = f"{category}.auto_{text_hash}"
        
        # Translate
        translated = translator.translate(key, lang, text)
        
        return jsonify({
            'original': text,
            'translated': translated,
            'language': lang,
            'key': key,
            'from_cache': translator.has_translation(key, lang)
        })
    
    # Add helper to app context for easy access
    app.translator = get_translator()
    
    # Log initialization
    app.logger.info("✅ Translation system initialized for Flask app")
    
    return app

# Helper function for standalone use
def create_translation_app(config=None):
    """
    Create a minimal Flask app with translation support for testing.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Flask application instance
    """
    from flask import Flask
    
    app = Flask(__name__)
    
    if config:
        app.config.update(config)
    
    # Initialize translation system
    init_app(app)
    
    # Add a test route
    @app.route('/test-translation')
    def test_translation():
        return """
        <h1>Translation System Test</h1>
        <p>Current language: {{ get_language() }}</p>
        <p>Test translation: {{ t('test_key', 'global', 'Default Test Text') }}</p>
        """
    
    return app
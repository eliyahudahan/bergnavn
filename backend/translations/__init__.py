"""
Complete dynamic translation system for BergNavn Maritime.
Automatically handles ALL text in ALL templates.
"""

from .core import (
    TranslationRegistry,
    get_registry,
    initialize_translations
)

from .flask_integration import (
    DynamicTranslator,
    get_translator,
    init_app
)

from .template_transformer import TemplateTransformer

__version__ = "1.0.0"
__all__ = [
    'TranslationRegistry',
    'DynamicTranslator',
    'TemplateTransformer',
    'get_registry',
    'get_translator',
    'init_app',
    'initialize_translations'
]

print("🌍 BergNavn Maritime Translation System v1.0.0 loaded")
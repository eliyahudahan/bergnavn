# backend/routes/main_routes.py
import logging
from flask import Blueprint, render_template, session, request
from backend.utils.helpers import get_current_language

main_bp = Blueprint("main_bp", __name__)
logger = logging.getLogger(__name__)


@main_bp.route("/")
@main_bp.route("/<lang>")
def home(lang=None):
    """
    Home page – multilingual support.
    """
    # Handle language from URL parameter
    if lang in ['en', 'no']:
        session['lang'] = lang
    
    current_lang = get_current_language()
    return render_template("home.html", lang=current_lang)


@main_bp.route("/legal")
def legal():
    """
    Legal / License page.
    """
    current_lang = get_current_language()
    return render_template("legal.html", lang=current_lang)


@main_bp.route("/about")
def about():
    """
    About page.
    """
    current_lang = get_current_language()
    return render_template("about.html", lang=current_lang)


@main_bp.route("/contact")
def contact():
    """
    Contact page.
    """
    current_lang = get_current_language()
    return render_template("contact.html", lang=current_lang)


@main_bp.route("/language/<lang>")
def change_language(lang):
    """
    Change application language.
    """
    if lang in ['en', 'no']:
        session['lang'] = lang
        return {'success': True, 'language': lang}
    return {'success': False, 'error': 'Unsupported language'}, 400
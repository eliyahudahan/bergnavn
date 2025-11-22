import logging
from flask import Blueprint, render_template
from backend.utils.helpers import get_current_language

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
@main_bp.route('/<lang>')
def home(lang=None):
    """
    Route: Home page with optional language parameter
    """
    current_lang = get_current_language()
    return render_template('home.html', lang=current_lang)

@main_bp.route('/legal')
def legal():
    """
    Route: Legal / License page
    """
    current_lang = get_current_language()
    return render_template('legal.html', lang=current_lang)
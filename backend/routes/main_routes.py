import logging
from flask import Blueprint, render_template
from backend.utils.helpers import get_current_language  # ✅ Import language helper

# Create a Blueprint for main pages (home, legal, etc.)
# Use 'main_bp' as the blueprint name to match url_for() calls in templates
main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def home():
    """
    Route: Home page
    Purpose: Render the main homepage.
    Logs the access to the terminal and logging system.
    """
    # Get current language from query/session
    lang = get_current_language()

    print(">>> home() was called – rendering home.html <<<")
    logging.info(">>> home() was called – rendering home.html <<<")
    return render_template('home.html', lang=lang)

@main_bp.route('/legal')
def legal():
    """
    Route: Legal / License page
    Purpose: Render the Open License / Compliance page.
    Notes:
        - Displays copyright information.
        - Shows attribution and compliance with Norwegian regulations.
        - Supports multilingual translations (EN/NO).
        - Safe to link in both navbar and footer.
    """
    # Get current language from query/session
    lang = get_current_language()

    print(">>> legal() was called – rendering legal.html <<<")
    logging.info(">>> legal() was called – rendering legal.html <<<")
    return render_template('legal.html', lang=lang)

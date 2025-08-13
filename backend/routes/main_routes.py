import logging
from flask import Blueprint, render_template

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
    print(">>> home() was called – rendering home.html <<<")
    logging.info(">>> home() was called – rendering home.html <<<")
    return render_template('home.html')

@main_bp.route('/legal')
def legal():
    """
    Route: Legal / License page
    Purpose: Render the Open License / Compliance page.
    Notes:
        - Displays copyright information.
        - Shows attribution and compliance with Norwegian regulations.
        - Can be extended for translations (EN/NO) in the future.
        - Safe to link in both navbar and footer.
    """
    print(">>> legal() was called – rendering legal.html <<<")
    logging.info(">>> legal() was called – rendering legal.html <<<")
    return render_template('legal.html')

import logging
from flask import Blueprint, render_template

# יוצרים Blueprint לדפי הבסיס
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # הדפסה לטרמינל כדי שנדע שהגענו לכאן
    print(">>> home() was called – rendering home.html <<<")
    logging.info(">>> home() was called – rendering home.html <<<")
    return render_template('home.html')

# backend/utils/helpers.py
from flask import request, session

def get_current_language():
    """
    Determine the UI language using the following priority:
    1) ?lang=<code> in query string (explicit user choice; also saved to session)
    2) 'lang' stored in session
    3) Default to 'en'
    """
    lang_param = request.args.get('lang')
    if lang_param:
        session['lang'] = lang_param
        return lang_param
    return session.get('lang', 'en')

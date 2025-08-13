# backend/utils/translations.py

# Translation dictionary, easily extendable
TRANSLATIONS = {
    'en': {
        'dummy_users_title': 'Dummy Users',
        'create_new_user': 'Create New User',
        'username': 'Username',
        'email': 'Email',
        'scenario': 'Scenario',
        'actions': 'Actions',
        'edit': 'Edit',
        'active': 'Active',
        'inactive': 'Inactive',
        'dashboard': 'Dashboard',
        'cruises': 'Cruises',
        'routes': 'Routes',
        'footer_credit': 'Powered by BergNavn Maritime Voyages',
        'license_legal': 'License / Legal',
    },
    'no': {  # Norwegian Bokmål
        'dummy_users_title': 'Dummybrukere',
        'create_new_user': 'Opprett ny bruker',
        'username': 'Brukernavn',
        'email': 'E-post',
        'scenario': 'Scenario',
        'actions': 'Handlinger',
        'edit': 'Rediger',
        'active': 'Aktiv',
        'inactive': 'Inaktiv',
        'dashboard': 'Dashbord',
        'cruises': 'Cruises',
        'routes': 'Ruter',
        'footer_credit': 'Drevet av BergNavn Maritime Voyages',
        'license_legal': 'Lisens / Juridisk',
    }
}

def translate(key: str, lang: str = 'en') -> str:
    """
    Return translated string for the given key and language.
    Defaults to English if key or language is not found.
    """
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

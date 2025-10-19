# translations.py
# English and Norwegian support for BergNavn

translations = {
    'en': {
        'global': {
            'dashboard': 'Dashboard',
            'cruises': 'Cruises',
            'routes': 'Routes',
            'back_to_home': 'Back to Home',
            'footer_credit': '© 2025 BergNavn Maritime',
            'not_available': 'N/A',
            'home_welcome': 'Welcome to BergNavn',
            'home_greeting': 'Your real-time maritime platform',
            'home_description': 'Track, analyze and optimize routes between Kristiansand and Oslo.',
            'home_navigation_info': 'Use the navigation buttons below to explore the platform.',
            'global_operations': 'Global Operations',
            'global_operations_desc': 'Monitor and optimize maritime traffic in real time.',
            'data_driven': 'Data Driven',
            'data_driven_desc': 'Analytics and forecasts based on real-time data.',
            'secure_platform': 'Secure Platform',
            'secure_platform_desc': 'Robust and secure infrastructure.'
        },
        'dashboard_page': {
            'title': 'Voyages Dashboard',
            'id': 'ID',
            'name': 'Name',
            'status': 'Status',
            'no_voyages': 'No voyages found'
        },
        'cruises_page': {
            'title': 'Available Cruises',
            'description': 'Description',
            'departure_date': 'Departure Date',
            'return_date': 'Return Date',
            'price_eur': 'Price (€)',
            'no_cruises_found': 'No cruises available'
        },
        'home_page': {
            'welcome_message': 'Welcome to BergNavn',
            'home_intro_text': 'Your real-time maritime platform',
            'view_cruises': 'View Cruises'
        }
    },
    'no': {
        'global': {
            'dashboard': 'Dashbord',
            'cruises': 'Cruiser',
            'routes': 'Ruter',
            'back_to_home': 'Tilbake til Hjem',
            'footer_credit': '© 2025 BergNavn Maritime',
            'not_available': 'Ikke tilgjengelig',
            'home_welcome': 'Velkommen til BergNavn',
            'home_greeting': 'Din sanntids maritime plattform',
            'home_description': 'Spor, analyser og optimaliser ruter mellom Kristiansand og Oslo.',
            'home_navigation_info': 'Bruk navigasjonsknappene nedenfor for å utforske plattformen.',
            'global_operations': 'Global Operasjoner',
            'global_operations_desc': 'Overvåk og optimaliser maritim trafikk i sanntid.',
            'data_driven': 'Datadrevet',
            'data_driven_desc': 'Analyse og prognoser basert på sanntidsdata.',
            'secure_platform': 'Sikker Plattform',
            'secure_platform_desc': 'Robust og sikker infrastruktur.'
        },
        'dashboard_page': {
            'title': 'Reiser Dashbord',
            'id': 'ID',
            'name': 'Navn',
            'status': 'Status',
            'no_voyages': 'Ingen reiser funnet'
        },
        'cruises_page': {
            'title': 'Tilgjengelige Cruiser',
            'description': 'Beskrivelse',
            'departure_date': 'Avreisedato',
            'return_date': 'Returdato',
            'price_eur': 'Pris (€)',
            'no_cruises_found': 'Ingen cruisetilbud'
        },
        'home_page': {
            'welcome_message': 'Velkommen til BergNavn',
            'home_intro_text': 'Din sanntids maritime plattform',
            'view_cruises': 'Se Cruisere'
        }
    }
}

def translate(key: str, lang: str = 'en', page: str = 'global') -> str:
    """Return translation for a given key, language, and page context."""
    return translations.get(lang, translations['en']).get(page, {}).get(key, key)

# translations.py
# English and Norwegian support for BergNavn Maritime
# Complete translation dictionary for maritime operations platform

translations = {
    'en': {
        'global': {
            'home': 'Home',
            'legal': 'Legal',
            'routes': 'Routes',
            'back_to_home': 'Back to Home',
            'footer_credit': '© 2025 BergNavn Maritime',
            'not_available': 'N/A',
            'home_welcome': 'Welcome to BergNavn',
            'home_greeting': 'Your real-time maritime platform',
            'home_description': 'Track, analyze and optimize routes between Kristiansand and Oslo.',
            'global_operations': 'Global Operations',
            'global_operations_desc': 'Monitor and optimize maritime traffic in real time.',
            'data_driven': 'Data Driven',
            'data_driven_desc': 'Analytics and forecasts based on real-time data.',
            'secure_platform': 'Secure Platform',
            'secure_platform_desc': 'Robust and secure infrastructure.',
            # Maritime translations
            'maritime_dashboard': 'Maritime Dashboard',
            'maritime_description': 'Real-time maritime tracking platform',
            'cargo_volume': 'Cargo Volume',
            'route_eta': 'Route ETA',
            'fuel_optimization': 'Fuel Optimization'
        },
        'home_page': {
            'welcome_message': 'Welcome to BergNavn',
            'home_intro_text': 'Your real-time maritime platform',
            'view_cruises': 'View Cruises'
        },
        'routes_page': {
            'routes_title': 'Maritime Routes',
            'route_id': 'Route ID',
            'route_name': 'Route Name', 
            'origin': 'Origin',
            'destination': 'Destination',
            'duration': 'Duration',
            'hours': 'hours',
            'no_routes_found': 'No routes found'
        },
        'legal_page': {
            'legal_title': 'Legal Information & Acknowledgments',
            'legal_text_1': 'BergNavn Maritime is a real-time maritime data platform that integrates official data sources from Norwegian authorities including Kystverket AIS data, SSB cargo statistics, MET Norway weather forecasts, and RouteInfo maritime routes.',
            'legal_text_2': 'All data is sourced from official Norwegian government APIs and used in compliance with their terms of service. The platform demonstrates advanced integration of real-time maritime data for route optimization and operational efficiency.',
            'legal_text_3': 'This professional maritime platform showcases modern web technologies and data science applications in the maritime industry.'
        },
        'maritime_page': {
            'title': 'Maritime Dashboard',
            'cargo_volume': 'Cargo Volume',
            'official_data': 'Official Data',
            'route_eta': 'Route ETA',
            'fuel_savings': 'Fuel Savings',
            'live_map': 'Live Maritime Map',
            'coming_soon': 'Coming Soon',
            'route_visualization': 'Route Visualization',
            'route_analytics': 'Route Analytics',
            'data_sources': 'Data Sources',
            'official_statistics': 'Official Statistics',
            'weather_forecasts': 'Weather Forecasts',
            'maritime_routes': 'Maritime Routes'
        }
    },
    'no': {
        'global': {
            'home': 'Hjem',
            'legal': 'Juridisk',
            'routes': 'Ruter',
            'back_to_home': 'Tilbake til Hjem',
            'footer_credit': '© 2025 BergNavn Maritime',
            'not_available': 'Ikke tilgjengelig',
            'home_welcome': 'Velkommen til BergNavn',
            'home_greeting': 'Din sanntids maritime plattform',
            'home_description': 'Spor, analyser og optimaliser ruter mellom Kristiansand og Oslo.',
            'global_operations': 'Global Operasjoner',
            'global_operations_desc': 'Overvåk og optimaliser maritim trafikk i sanntid.',
            'data_driven': 'Datadrevet',
            'data_driven_desc': 'Analyse og prognoser basert på sanntidsdata.',
            'secure_platform': 'Sikker Plattform',
            'secure_platform_desc': 'Robust og sikker infrastruktur.',
            # Maritime translations in Norwegian
            'maritime_dashboard': 'Maritim Dashbord',
            'maritime_description': 'Sanntids maritim sporing',
            'cargo_volume': 'Godsvolum',
            'route_eta': 'Rute ETA',
            'fuel_optimization': 'Drivstoffoptimalisering'
        },
        'home_page': {
            'welcome_message': 'Velkommen til BergNavn',
            'home_intro_text': 'Din sanntids maritime plattform',
            'view_cruises': 'Se Cruisere'
        },
        'routes_page': {
            'routes_title': 'Maritime Ruter',
            'route_id': 'Rute ID',
            'route_name': 'Rute Navn',
            'origin': 'Opprinnelse',
            'destination': 'Destinasjon',
            'duration': 'Varighet',
            'hours': 'timer',
            'no_routes_found': 'Ingen ruter funnet'
        },
        'legal_page': {
            'legal_title': 'Juridisk Informasjon & Anerkjennelser',
            'legal_text_1': 'BergNavn Maritime er en sanntids maritim dataplattform som integrerer offisielle datakilder fra norske myndigheter inkludert Kystverket AIS-data, SSB godsstatistikk, MET Norge værmeldinger og RouteInfo maritime ruter.',
            'legal_text_2': 'All data er hentet fra offisielle norske statlige APIer og brukes i samsvar med deres vilkår for bruk. Plattformen demonstrerer avansert integrasjon av sanntids maritime data for ruteoptimalisering og operasjonell effektivitet.',
            'legal_text_3': 'Denne profesjonelle maritime plattformen viser moderne webteknologier og data science-applikasjoner i maritim industri.'
        },
        'maritime_page': {
            'title': 'Maritim Dashbord',
            'cargo_volume': 'Godsvolum',
            'official_data': 'Offisielle Data',
            'route_eta': 'Rute ETA',
            'fuel_savings': 'Drivstoffbesparelser',
            'live_map': 'Sanntids Maritim Kart',
            'coming_soon': 'Kommer Snart',
            'route_visualization': 'Rutevisualisering',
            'route_analytics': 'Ruteanalyse',
            'data_sources': 'Datakilder',
            'official_statistics': 'Offisiell Statistikk',
            'weather_forecasts': 'Værmeldinger',
            'maritime_routes': 'Maritime Ruter'
        }
    }
}

def translate(key: str, lang: str = 'en', page: str = 'global') -> str:
    """
    Return translation for a given key, language, and page context.
    
    Args:
        key: The translation key to look up
        lang: Language code ('en' or 'no')
        page: Page context for the translation
    
    Returns:
        Translated string or the original key if translation not found
    """
    return translations.get(lang, translations['en']).get(page, {}).get(key, key)
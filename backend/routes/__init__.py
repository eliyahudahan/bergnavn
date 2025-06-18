from .cruise_routes import cruise_blueprint  # ✅ Right name

def register_routes(app):
    app.register_blueprint(cruise_blueprint, url_prefix='/api')

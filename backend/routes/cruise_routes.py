from flask import Blueprint

cruise_blueprint = Blueprint('cruise', __name__)

# כל הנתיבים של הפלגות
@cruise_blueprint.route('/cruise')
def cruise():
    return "Cruise page"

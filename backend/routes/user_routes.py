from flask import Blueprint

# Create a Blueprint for user-related routes
user_blueprint = Blueprint('user', __name__)

# Route to get a list of users
@user_blueprint.route('/users', methods=['GET'])
def get_users():
    """
    Route: GET /users
    Purpose: Return a list of all users.
    Currently returns a placeholder string.
    """
    return "List of users"

# Route for the user home page
@user_blueprint.route('/users/home')
def home():
    """
    Route: GET /users/home
    Purpose: Return a welcome message for the Bergnavn API.
    Can be extended in the future to render a template.
    """
    return "Welcome to the Bergnavn API 🎉"

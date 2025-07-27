from flask import Blueprint

# יצירת Blueprint
user_blueprint = Blueprint('user', __name__)

# הגדרת נתיב (route)
@user_blueprint.route('/users', methods=['GET'])
def get_users():
    return "List of users"

@user_blueprint.route('/users/home')
def home():
    return "Welcome to the Bergnavn API 🎉"

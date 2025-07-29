from flask import Blueprint, request, jsonify
from backend.services.dummy_user_service import *

dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')

@dummy_user_bp.route('/', methods=['GET'])
def list_dummy_users():
    users = get_all_dummy_users()
    return jsonify([{'id': u.id, 'username': u.username, 'scenario': u.scenario} for u in users])

@dummy_user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    user = create_dummy_user(
        username=data['username'],
        email=data.get('email'),
        scenario=data.get('scenario'),
        flags=data.get('flags', {}),
        gender=data.get('gender'),
        nationality=data.get('nationality'),
        language=data.get('language'),
        preferred_sailing_areas=data.get('preferred_sailing_areas')
    )
    return jsonify({'id': user.id, 'username': user.username})


from flask import Blueprint, request, jsonify
from backend.services.dummy_user_service import (
    get_all_dummy_users,
    create_dummy_user,
    update_dummy_user,
    deactivate_dummy_user,
    get_dummy_user_by_id
)

dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')

# שליפה של כל המשתמשים
@dummy_user_bp.route('/', methods=['GET'])
def list_dummy_users():
    users = get_all_dummy_users()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'scenario': u.scenario,
            'email': u.email,
            'active': u.active,
            'flags': u.flags,
            'gender': u.gender,
            'nationality': u.nationality,
            'language': u.language,
            'preferred_sailing_areas': u.preferred_sailing_areas,
        }
        for u in users
    ])

# יצירת משתמש חדש
@dummy_user_bp.route('/', methods=['POST'])
def create_user():
    data = request.get_json()
    try:
        user = create_dummy_user(
            username=data['username'],
            email=data.get('email'),
            scenario=data.get('scenario'),
            user_flags=data.get('flags', {}),
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            language=data.get('language'),
            preferred_sailing_areas=data.get('preferred_sailing_areas')
        )
        return jsonify({'id': user.id, 'username': user.username}), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400

# עדכון משתמש לפי ID
@dummy_user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    success = update_dummy_user(user_id, data)
    if success:
        return jsonify({'message': 'User updated'})
    else:
        return jsonify({'error': 'User not found or inactive'}), 404

# מחיקת משתמש (השבתה לוגית)
@dummy_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    success = deactivate_dummy_user(user_id)
    if success:
        return jsonify({'message': 'User deactivated'})
    else:
        return jsonify({'error': 'User not found or already inactive'}), 404

# שליפה לפי ID
@dummy_user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_dummy_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'scenario': user.scenario,
        'email': user.email,
        'active': user.active,
        'flags': user.flags,
        'gender': user.gender,
        'nationality': user.nationality,
        'language': user.language,
        'preferred_sailing_areas': user.preferred_sailing_areas,
    })


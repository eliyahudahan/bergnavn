from flask import render_template, Blueprint, request, jsonify, redirect, url_for
from backend.services.dummy_user_service import (
    get_all_dummy_users,
    create_dummy_user,
    update_dummy_user,
    deactivate_dummy_user,
    get_dummy_user_by_id
)

dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')

# Main UI page: list all dummy users
@dummy_user_bp.route('/ui', methods=['GET'])
def dummy_user_ui():
    users = get_all_dummy_users()
    message = request.args.get('message')
    error = request.args.get('error')
    return render_template('dummy_users.html', users=users, message=message, error=error)

# Edit form for a specific user (GET)
@dummy_user_bp.route('/edit/<int:user_id>', methods=['GET'])
def edit_user_form(user_id):
    user = get_dummy_user_by_id(user_id)
    if not user:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error="User not found."))
    return render_template('edit_dummy_user.html', user=user)

# Get all dummy users as JSON
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

# Create a new user from form submission
@dummy_user_bp.route('/form', methods=['POST'])
def create_user_from_form():
    data = request.form
    try:
        preferred_areas = [area.strip() for area in data.get('preferred_sailing_areas', '').split(',') if area.strip()]
        
        user = create_dummy_user(
            username=data['username'],
            email=data.get('email'),
            scenario=data.get('scenario'),
            user_flags={},  # can be expanded in the future
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            language=data.get('language'),
            preferred_sailing_areas=preferred_areas
        )
        return redirect(url_for('dummy_user_bp.dummy_user_ui', message="User created successfully!"))

    except ValueError as e:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error=str(e)))

# Update a user by ID (from edit form)
@dummy_user_bp.route('/edit/<int:user_id>', methods=['POST'])
def update_dummy_user_form(user_id):
    data = request.form
    preferred_areas = [area.strip() for area in data.get('preferred_sailing_areas', '').split(',') if area.strip()]
    
    update_data = {
        'username': data.get('username'),
        'email': data.get('email'),
        'scenario': data.get('scenario'),
        'gender': data.get('gender'),
        'nationality': data.get('nationality'),
        'language': data.get('language'),
        'preferred_sailing_areas': preferred_areas,
    }

    success = update_dummy_user(user_id, update_data)

    if success:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', message="User updated successfully!"))
    else:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error="User not found or is inactive."))

# Deactivate (soft-delete) a user
@dummy_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    success = deactivate_dummy_user(user_id)
    if success:
        return jsonify({'message': 'User deactivated'})
    else:
        return jsonify({'error': 'User not found or already inactive'}), 404

# Get a specific user by ID (JSON format)
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




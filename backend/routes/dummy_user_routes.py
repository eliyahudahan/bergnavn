import re
from flask import render_template, Blueprint, request, jsonify, redirect, url_for, current_app
from backend.services.dummy_user_service import (
    get_all_dummy_users,
    create_dummy_user,
    update_dummy_user,
    deactivate_dummy_user,
    get_dummy_user_by_id,
    toggle_dummy_user_active
)

dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')


@dummy_user_bp.route('/ui', methods=['GET'])
def dummy_user_ui():
    filter_status = request.args.get('filter', 'active')  #Default:only active users
    users = get_all_dummy_users(filter_status)
    message = request.args.get('message')
    error = request.args.get('error')
    return render_template('dummy_users.html', users=users, message=message, error=error, filter_status=filter_status)


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


# Create a new dummy user from form submission with validation
@dummy_user_bp.route('/form', methods=['POST'])
def create_user_from_form():
    data = request.form

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    if not username:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error="Username is required."))

    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if email and not re.match(email_regex, email):
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error="Invalid email address."))

    preferred_areas = [area.strip() for area in data.get('preferred_sailing_areas', '').split(',') if area.strip()]

    if len(preferred_areas) > 3:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error="You can specify up to 3 preferred sailing areas only."))

    try:
        create_dummy_user(
            username=username,
            email=email if email else None,
            scenario=data.get('scenario'),
            user_flags={},
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

    if len(preferred_areas) > 3:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id,
                                error="You can specify up to 3 preferred sailing areas only."))

    update_data = {
        'username': data.get('username', '').strip(),
        'email': data.get('email', '').strip(),
        'scenario': data.get('scenario'),
        'gender': data.get('gender'),
        'nationality': data.get('nationality'),
        'language': data.get('language'),
        'preferred_sailing_areas': preferred_areas,
    }

    if not update_data['username']:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error="Username is required."))

    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if update_data['email'] and not re.match(email_regex, update_data['email']):
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error="Invalid email address."))

    try:
        success = update_dummy_user(user_id, update_data)
        if success:
            return redirect(url_for('dummy_user_bp.dummy_user_ui', message="User updated successfully!"))
        else:
            return redirect(url_for('dummy_user_bp.dummy_user_ui', error="User not found or is inactive."))
    except ValueError as e:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error=str(e)))


# Toggle active/inactive status of user
@dummy_user_bp.route('/toggle/<int:user_id>', methods=['POST'])
def toggle_user_active(user_id):
    # Optional: Add authentication/admin check here
    set_active = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        if 'active' in payload:
            set_active = bool(payload['active'])

    try:
        user = toggle_dummy_user_active(user_id, set_active)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'success': True, 'active': bool(user.active)}), 200
    except ValueError as e:
        current_app.logger.exception("Toggle failed")
        return jsonify({'error': str(e)}), 500


# Show create user form
@dummy_user_bp.route('/create', methods=['GET'])
def show_create_user_form():
    error = request.args.get('error')
    message = request.args.get('message')
    return render_template('create_dummy_user.html', error=error, message=message)


# Deactivate (soft-delete) a user
@dummy_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    success = deactivate_dummy_user(user_id)
    if success:
        return jsonify({'message': 'User deactivated'})
    else:
        return jsonify({'error': 'User not found or already inactive'}), 404


# Get a specific user by ID (JSON)
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

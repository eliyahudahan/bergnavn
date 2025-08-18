import re
from flask import render_template, Blueprint, request, jsonify, redirect, url_for, current_app, session
from backend.services.dummy_user_service import (
    get_all_dummy_users,
    create_dummy_user,
    update_dummy_user,
    deactivate_dummy_user,
    get_dummy_user_by_id,
    toggle_dummy_user_active
)
from backend.utils.translations import translate

dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')

# --- UI page ---
@dummy_user_bp.route('/ui', methods=['GET'])
def dummy_user_ui():
    """Show all dummy users page"""
    filter_status = request.args.get('filter', 'active')
    users = get_all_dummy_users(filter_status)
    message = request.args.get('message')
    error = request.args.get('error')
    lang = session.get('lang', 'en')
    return render_template(
        'dummy_users.html',
        users=users,
        message=message,
        error=error,
        filter_status=filter_status,
        lang=lang
    )

# --- Show create form ---
@dummy_user_bp.route('/create', methods=['GET'])
def show_create_user_form():
    """Show the form to create a new dummy user"""
    error = request.args.get('error')
    message = request.args.get('message')
    lang = session.get('lang', 'en')
    return render_template('create_dummy_user.html', error=error, message=message, lang=lang)

# --- Create user form submission ---
@dummy_user_bp.route('/form', methods=['POST'])
def create_user_from_form():
    """Handle form submission for creating dummy user"""
    all_users = get_all_dummy_users()
    lang = session.get('lang', 'en')

    # Limit max 5 dummy users
    if len(all_users) >= 5:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error=translate('limit_dummy', lang)))

    data = request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    if not username:
        return redirect(url_for('dummy_user_bp.show_create_user_form', error=translate('username_required', lang)))

    # Validate email
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if email and not re.match(email_regex, email):
        return redirect(url_for('dummy_user_bp.show_create_user_form', error=translate('invalid_email', lang)))

    preferred_areas = [a.strip() for a in data.get('preferred_sailing_areas', '').split(',') if a.strip()]
    if len(preferred_areas) > 3:
        return redirect(url_for('dummy_user_bp.show_create_user_form', error=translate('preferred_areas_limit', lang)))

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
        return redirect(url_for('dummy_user_bp.dummy_user_ui', message=translate('user_created', lang)))
    except ValueError as e:
        return redirect(url_for('dummy_user_bp.show_create_user_form', error=str(e)))

# --- Edit user GET ---
@dummy_user_bp.route('/edit/<int:user_id>', methods=['GET'])
def edit_user_form(user_id):
    """Show edit form for a specific user"""
    user = get_dummy_user_by_id(user_id)
    lang = session.get('lang', 'en')
    if not user:
        return redirect(url_for('dummy_user_bp.dummy_user_ui', error=translate('user_not_found', lang)))
    return render_template('edit_dummy_user.html', user=user, lang=lang)

# --- Edit user POST ---
@dummy_user_bp.route('/edit/<int:user_id>', methods=['POST'])
def update_dummy_user_form(user_id):
    """Handle edit form submission"""
    data = request.form
    lang = session.get('lang', 'en')
    preferred_areas = [a.strip() for a in data.get('preferred_sailing_areas', '').split(',') if a.strip()]

    if len(preferred_areas) > 3:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id,
                                error=translate('preferred_areas_limit', lang)))

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
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error=translate('username_required', lang)))

    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if update_data['email'] and not re.match(email_regex, update_data['email']):
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error=translate('invalid_email', lang)))

    try:
        success = update_dummy_user(user_id, update_data)
        if success:
            return redirect(url_for('dummy_user_bp.dummy_user_ui', message=translate('user_updated', lang)))
        else:
            return redirect(url_for('dummy_user_bp.dummy_user_ui', error=translate('user_not_found', lang)))
    except ValueError as e:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error=str(e)))

# --- Toggle active/inactive ---
@dummy_user_bp.route('/toggle/<int:user_id>', methods=['POST'])
def toggle_user_active(user_id):
    """Toggle active status via JSON request"""
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

# --- Delete user (soft) ---
@dummy_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Soft-delete a dummy user"""
    success = deactivate_dummy_user(user_id)
    if success:
        return jsonify({'message': 'User deactivated'})
    else:
        return jsonify({'error': 'User not found or already inactive'}), 404

# --- Get specific user JSON ---
@dummy_user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Return specific user as JSON"""
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

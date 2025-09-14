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

# Blueprint for dummy user management
dummy_user_bp = Blueprint('dummy_user_bp', __name__, url_prefix='/dummy-users')


# --- UI page: Display all dummy users ---
@dummy_user_bp.route('/ui', methods=['GET'])
def dummy_user_ui():
    """
    Render the main dummy users page.
    Allows optional filtering by status: 'active', 'inactive', or 'all'.
    Passes messages and errors from query parameters.
    """
    filter_status = request.args.get('filter', 'active')
    users = get_all_dummy_users(filter_status)
    message = request.args.get('message')
    error = request.args.get('error')
    lang = session.get('lang', 'en')  # Fetch user's preferred language

    return render_template(
        'dummy_users.html',
        users=users,
        message=message,
        error=error,
        filter_status=filter_status,
        lang=lang
    )


# --- Show form to create a new dummy user ---
@dummy_user_bp.route('/create', methods=['GET'])
def show_create_user_form():
    """
    Display the form for creating a new dummy user.
    Includes optional error/message feedback.
    """
    error = request.args.get('error')
    message = request.args.get('message')
    lang = session.get('lang', 'en')

    return render_template('create_dummy_user.html', error=error, message=message, lang=lang)


# --- Handle form submission for creating dummy user ---
@dummy_user_bp.route('/form', methods=['POST'])
def create_user_from_form():
    """
    Processes POST request from the create user form.
    Validates username, email format, preferred sailing areas.
    Limits maximum number of dummy users to 5.
    Creates the user via service and redirects with translated messages.
    """
    lang = session.get('lang', 'en')
    data = request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    preferred_areas = [a.strip() for a in data.get('preferred_sailing_areas', '').split(',') if a.strip()]

    # Validation: username required
    if not username:
        return redirect(
            url_for('dummy_user_bp.show_create_user_form',
                    error=translate('username_required', lang, 'dummy_users'))
        )

    # Validation: maximum 3 preferred sailing areas
    if len(preferred_areas) > 3:
        return redirect(
            url_for('dummy_user_bp.show_create_user_form',
                    error=translate('preferred_areas_limit', lang, 'dummy_users'))
        )

    # Validation: email format
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if email and not re.match(email_regex, email):
        return redirect(
            url_for('dummy_user_bp.show_create_user_form',
                    error=translate('invalid_email', lang, 'dummy_users'))
        )

    try:
        create_dummy_user(
            username=username,
            email=email if email else None,
            scenario=data.get('scenario'),
            user_flags={},
            gender=data.get('gender'),
            nationality=data.get('nationality'),
            language=data.get('language'),
            preferred_sailing_areas=preferred_areas,
            lang=lang
        )
        return redirect(
            url_for('dummy_user_bp.dummy_user_ui',
                    message=translate('user_created', lang, 'dummy_users'))
        )
    except ValueError as e:
        return redirect(url_for('dummy_user_bp.show_create_user_form', error=str(e)))


# --- Show form to edit an existing dummy user ---
@dummy_user_bp.route('/edit/<int:user_id>', methods=['GET'])
def edit_user_form(user_id):
    """
    Display edit form for a specific user.
    Shows error if user not found.
    """
    lang = session.get('lang', 'en')
    user = get_dummy_user_by_id(user_id)
    if not user:
        return redirect(
            url_for('dummy_user_bp.dummy_user_ui', error=translate('user_not_found', lang, 'dummy_users'))
        )

    return render_template('edit_dummy_user.html', user=user, lang=lang)


# --- Handle POST request to update an existing dummy user ---
@dummy_user_bp.route('/edit/<int:user_id>', methods=['POST'])
def update_dummy_user_form(user_id):
    """
    Processes edit form submission.
    Validates username, email format, preferred sailing areas.
    Updates user via service and redirects with translated messages.
    """
    lang = session.get('lang', 'en')
    data = request.form
    preferred_areas = [a.strip() for a in data.get('preferred_sailing_areas', '').split(',') if a.strip()]

    if len(preferred_areas) > 3:
        return redirect(
            url_for('dummy_user_bp.edit_user_form',
                    user_id=user_id,
                    error=translate('preferred_areas_limit', lang, 'dummy_users'))
        )

    update_data = {
        'username': data.get('username', '').strip(),
        'email': data.get('email', '').strip(),
        'scenario': data.get('scenario'),
        'gender': data.get('gender'),
        'nationality': data.get('nationality'),
        'language': data.get('language'),
        'preferred_sailing_areas': preferred_areas,
    }

    # Validation: username required
    if not update_data['username']:
        return redirect(
            url_for('dummy_user_bp.edit_user_form',
                    user_id=user_id,
                    error=translate('username_required', lang, 'dummy_users'))
        )

    # Validation: email format
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if update_data['email'] and not re.match(email_regex, update_data['email']):
        return redirect(
            url_for('dummy_user_bp.edit_user_form',
                    user_id=user_id,
                    error=translate('invalid_email', lang, 'dummy_users'))
        )

    try:
        update_dummy_user(user_id, update_data, lang=lang)
        return redirect(
            url_for('dummy_user_bp.dummy_user_ui',
                    message=translate('user_updated', lang, 'dummy_users'))
        )
    except ValueError as e:
        return redirect(url_for('dummy_user_bp.edit_user_form', user_id=user_id, error=str(e)))


# --- Toggle active/inactive status of a user ---
@dummy_user_bp.route('/toggle/<int:user_id>', methods=['POST'])
def toggle_user_active(user_id):
    """
    Toggle the active/inactive status via JSON POST request.
    Returns JSON with success and updated status.
    """
    lang = session.get('lang', 'en')
    set_active = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        if 'active' in payload:
            set_active = bool(payload['active'])

    try:
        user = toggle_dummy_user_active(user_id, set_active, lang=lang)
        return jsonify({'success': True, 'active': bool(user.active)}), 200
    except ValueError as e:
        current_app.logger.exception("Toggle failed")
        return jsonify({'error': str(e)}), 404


# --- Soft delete a dummy user ---
@dummy_user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Soft-delete a dummy user by marking inactive.
    Returns JSON with success/error message in user's language.
    """
    lang = session.get('lang', 'en')
    try:
        deactivate_dummy_user(user_id, lang=lang)
        return jsonify({'message': translate('user_deactivated', lang, 'dummy_users')})
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# --- Get a specific user as JSON ---
@dummy_user_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """
    Return a specific user as JSON.
    Includes all fields and preferred sailing areas.
    If not found, returns 404 with translated message.
    """
    user = get_dummy_user_by_id(user_id)
    if not user:
        lang = session.get('lang', 'en')
        return jsonify({'error': translate('user_not_found', lang, 'dummy_users')}), 404

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

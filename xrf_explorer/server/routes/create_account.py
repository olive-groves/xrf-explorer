from flask import request, jsonify
from xrf_explorer import app, auth, db
from xrf_explorer.server.database.models import User, UserRole

@auth.login_required(role=UserRole.ADMIN)
@app.route('/api/create_account', methods=['POST'])
def create_account():
    """
    Given a username, password, and role, create a new user account and add it to the database.
    :return: JSON success or failure message
    """
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role_str = data.get('role')

    # Check if the username, password, and role are provided
    if not username or not password or not role_str:
        return jsonify({"success": False, "message": "Missing username, password, or role"}), 400

    # Validate the role
    try:
        role = UserRole[role_str]
    except KeyError:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    # Check if the username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 409

    # Create a new user
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "Account created successfully"}), 201

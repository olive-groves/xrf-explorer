from flask import request, jsonify
from xrf_explorer import app, auth, db
from xrf_explorer.server.database.models import User, UserRole

@auth.login_required(role=UserRole.ADMIN)
@app.route('/api/update_account', methods=['POST'])
def update_account():
    """
    Update an existing user account.
    :return: JSON success or failure message
    """
    
    data = request.json
    originalUsername = data.get('originalUsername')
    username = data.get('username')
    password = data.get('password')
    role_str = data.get('role')

    # Check if the username and role are provided
    if not username or not role_str:
        return jsonify({"success": False, "message": "Missing username or role"}), 400

    # Validate the role
    try:
        role = UserRole[role_str]
    except KeyError:
        return jsonify({"success": False, "message": "Invalid role"}), 400

    # Check if the user is already in the database
    if User.query.filter_by(username=username).first() and (username != originalUsername):
        return jsonify({"success": False, "message": "Username already exists"}), 409

    # Update the user's username, password and role
    user = User.query.filter_by(username=originalUsername).first()
    user.username = username
    user.role = role
    if (password): 
        user.set_password(password)
    db.session.commit()

    return jsonify({"success": True, "message": "Account updated successfully"}), 200

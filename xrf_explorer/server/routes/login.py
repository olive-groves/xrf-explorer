from flask import request, jsonify
from xrf_explorer import app
from xrf_explorer.server.database.models import User
import flask_login
from flask_login import login_user, current_user


@app.route('/api/login', methods=['POST'])
def login():
    """
    Takes a username and password, verifies them, and returns a success or failure message.
    :return: JSON success or failure message
    """
    
    # Get the username and password from the request
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Check if the username and password are provided
    if not username or not password:
        return jsonify({"success": False, "message": "Missing username or password"}), 400

    # Find the user in the database
    user = User.query.filter_by(username=username).first()
    
    # Verify the password
    if user and user.check_password(password):

        #create and send cookie to client
        flask_login.login_user(user)

        # return jsonify({"success": True, "message": "Login successful", "role": user.role.name, "token": token}), 200
        return jsonify({"success": True, "message": "Login successful", "username": user.username, "role": user.role.name, "projects": user.getProjects()}), 200
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


@app.route('/api/me', methods=['GET'])
def me():
    if not current_user.is_authenticated:
        return jsonify({
        "authenticated": False,
        "username": "",
        "role": "",
        "projects": []
    }), 200
    return jsonify({
        "authenticated": True,
        "username": current_user.username,
        "role": current_user.role.name,
        "projects": current_user.getProjects()
    }), 200

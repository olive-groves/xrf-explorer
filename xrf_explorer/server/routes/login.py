from flask import request, jsonify
from xrf_explorer import app
from xrf_explorer.server.database.models import User

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
        # token = user.generate_auth_token()

        # return jsonify({"success": True, "message": "Login successful", "role": user.role.name, "token": token}), 200
        return jsonify({"success": True, "message": "Login successful", "username": user.username, "role": user.role.name}), 200
    return jsonify({"success": False, "message": "Invalid username or password"}), 401
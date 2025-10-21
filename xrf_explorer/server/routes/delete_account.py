from flask import request, jsonify
from xrf_explorer import app, auth, db
from xrf_explorer.server.database.models import User, UserRole

@auth.login_required(role=UserRole.ADMIN)
@app.route('/api/delete_account', methods=['POST'])
def delete_account():
    """
    Given a username, delete the user account from the database.
    :return: JSON success or failure message
    """
    
    data = request.json
    username = data.get('username')

    # Check if the username is provided
    if not username:
        return jsonify({"success": False, "message": "Missing username"}), 400

    # Find the user by username
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    # Delete the user account
    db.session.delete(user)
    db.session.commit()

    return jsonify({"success": True, "message": "Account deleted successfully"}), 200
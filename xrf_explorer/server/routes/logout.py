from flask import request, jsonify
from flask_login import login_required, logout_user
from xrf_explorer import app

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    """
    Tries to log a user out and returns a success or failure message.
    :return: JSON success or failure message
    """

    try:
        logout_user()
        return jsonify({"success": True}), 200


    except Exception as e:
        return jsonify({"success": False}), 401



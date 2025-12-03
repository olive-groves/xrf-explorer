from flask import jsonify
from flask_login import login_required
from xrf_explorer import app
from xrf_explorer.server.database.authnew import admin_required
from xrf_explorer.server.database.models import User


@app.route('/api/projects/<username>', methods=['GET'])
@login_required
@admin_required
def get_projects(username: str):
    """
    Retrieve a list of all projects user has access to.
    :return: JSON list of projects
    """

    # Check if the username is provided
    if not username:
        return jsonify({"success": False, "message": "Missing username"}), 400

    # Query the user from the database
    user = User.query.filter_by(username=username).first()

    # Return projects the user has access to
    return jsonify(user.projects), 200
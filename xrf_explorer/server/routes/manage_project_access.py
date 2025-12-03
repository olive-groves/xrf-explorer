from flask import request, jsonify
from flask_login import login_required
from xrf_explorer import app, db
from xrf_explorer.server.database.authnew import admin_required
from xrf_explorer.server.database.models import User
from sqlalchemy.orm.attributes import flag_modified

@app.route('/api/grant_project_access', methods=['POST'])
@login_required
@admin_required
def grant_project_access():
    """
    Grant access to a project for a user.
    :return: JSON success or failure message
    """
    
    # Get the username and project from the request
    data = request.json
    username = data.get('username')
    project = data.get('project')

    # Check if the username and project are provided
    if not username or not project:
        return jsonify({"success": False, "message": "Missing username or project"}), 400
    
    user = User.query.filter_by(username=username).first()

    # Check if the user already has access to the project
    if user and user.checkProjectAccess(project):
        return jsonify({"success": False, "message": "User already has access to this project"}), 409

    # Update the user's projects
    user.giveProjectAccess(project)

    return jsonify({"success": True, "message": "Access granted successfully"}), 200

@app.route('/api/revoke_project_access', methods=['POST'])
@login_required
@admin_required
def revoke_project_access():
    """
    Revoke access to a project for a user.
    :return: JSON success or failure message
    """
    
    # Get the username and project from the request
    data = request.json
    username = data.get('username')
    project = data.get('project')

    # Check if the username and project are provided
    if not username or not project:
        return jsonify({"success": False, "message": "Missing username or project"}), 400

    user = User.query.filter_by(username=username).first()
    # Check if the user has access to the project
    if user and not user.checkProjectAccess(project):
        return jsonify({"success": False, "message": "User does not have access to this project"}), 409

    user.revokeProjectAccess(project)


    return jsonify({"success": True, "message": "Access revoked successfully"}), 200

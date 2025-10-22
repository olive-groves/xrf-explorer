from flask import jsonify
from flask_login import login_required
from xrf_explorer import app, auth
from xrf_explorer.server.database.authnew import admin_required
from xrf_explorer.server.database.models import User, UserRole


@app.route('/api/accounts', methods=['GET'])
@login_required
@admin_required
def get_accounts():
    """
    Retrieve a list of all user accounts.
    :return: JSON list of user accounts with usernames and roles
    """
    
    accounts = User.query.all()
    return jsonify([{"username": acc.username, "role": acc.role.name.capitalize()} for acc in accounts]), 200

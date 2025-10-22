from functools import wraps
from flask import current_app, jsonify
from flask_login import current_user
from xrf_explorer.server.database.models import User


login_manager = flask_login.LoginManager()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return jsonify({"success": False, "message": "Unauthorized"}), 401

def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not current_user.isAdmin():
            return current_app.login_manager.unauthorized()
        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view

def editor_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_app.config.get("LOGIN_DISABLED"):
            pass
        elif not (current_user.isEditor()):
            return current_app.login_manager.unauthorized()
        # flask 1.x compatibility
        # current_app.ensure_sync is only available in Flask >= 2.0
        if callable(getattr(current_app, "ensure_sync", None)):
            return current_app.ensure_sync(func)(*args, **kwargs)
        return func(*args, **kwargs)

    return decorated_view




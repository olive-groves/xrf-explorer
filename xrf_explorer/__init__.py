# Import the necessary modules and create the Flask app
from pathlib import Path
from flask import Flask, send_from_directory
import flask_login
from xrf_explorer.server.database.authnew import login_manager
from flask_cors import CORS
from xrf_explorer.server.database.database import init_app
from xrf_explorer.server.database.models import User  # Ensure models are imported
from xrf_explorer.server.database.models import UserRole

from logging import getLogger, Logger

LOG: Logger = getLogger(__name__)
# Create the Flask app
app: Flask = Flask(__name__, template_folder=Path('client/templates'), static_folder='client/dist')

if not Path("xrf_explorer/secret_key.txt").exists():
    # Generate a new secret key and save it to the file
    import os
    secret_key = os.urandom(24)
    with open("xrf_explorer/secret_key.txt", 'wb') as file:
        file.write(secret_key)

with open("xrf_explorer/secret_key.txt", 'r') as file:
    app.secret_key = file.read()

login_manager.init_app(app)

# Enable CORS for the app
CORS(app)

# Initialize the database
db = init_app(app)

def add_and_commit_user(user: User):
    db.session.add(user)
    db.session.commit()

# Create the database tables and a default admin user if none exist
with app.app_context():
    db.create_all()  # Create database tables for our data models
    
    # Create a default admin user if none exist
    if not User.query.filter_by(role=UserRole.ADMIN).first():
        admin_user = User(username='admin', role=UserRole.ADMIN)
        admin_user.set_password('admin')  # Set a default password; should be changed after first login
        add_and_commit_user(admin_user)
        LOG.info("Database initialized with default admin user.")
    else:
        LOG.info("Admin user already exists.")
    
    # Create a default viewer user if none exist
    if not User.query.filter_by(role=UserRole.VIEWER).first():
        viewer_user = User(username='viewer', role=UserRole.VIEWER)
        viewer_user.set_password('viewer')
        add_and_commit_user(viewer_user)
        LOG.info("Database initialized with default viewer user.")
    else:
        LOG.info("Viewer user already exists.")

    # Create a default viewer user if none exist
    if not User.query.filter_by(role=UserRole.EDITOR).first():
        editor_user = User(username='editor', role=UserRole.EDITOR)
        editor_user.set_password('editor')
        add_and_commit_user(editor_user)
        LOG.info("Database initialized with default editor user.")
    else:
        LOG.info("Editor user already exists.")

# Import and register the routes
from xrf_explorer.server.routes import *

# All routes not matched in the server are forwarded to the client
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(Path('client/dist'), path)

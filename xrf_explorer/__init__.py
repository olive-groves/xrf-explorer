# Import the necessary modules and create the Flask app
from pathlib import Path
from flask import Flask, send_from_directory
import flask_login
from xrf_explorer.server.database.authnew import login_manager
from flask_cors import CORS
from xrf_explorer.server.database.database import init_app
from xrf_explorer.server.database.models import User  # Ensure models are imported
from xrf_explorer.server.database.models import UserRole

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

# Create the database tables and a default admin user if none exist
with app.app_context():
    db.create_all()  # Create database tables for our data models
    
    # Create a default admin user if none exist
    if not User.query.filter_by(role=UserRole.ADMIN).first():
        admin_user = User(username='admin', role=UserRole.ADMIN)
        admin_user.set_password('testpassword')  # Set a default password; should be changed after first login
        db.session.add(admin_user)
        db.session.commit()
        print("Database initialized with default admin user.")
    else:
        print("Admin user already exists.")
    
    # Create a default viewer user if none exist
    if not User.query.filter_by(role=UserRole.VIEWER).first():
        viewer_user = User(username='viewer', role=UserRole.VIEWER)
        viewer_user.set_password('viewerpassword')
        db.session.add(viewer_user)
        db.session.commit()
        print("Database initialized with default viewer user.")
    else:
        print("Viewer user already exists.")

# Import and register the routes
from xrf_explorer.server.routes import *

# All routes not matched in the server are forwarded to the client
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(Path('client/dist'), path)

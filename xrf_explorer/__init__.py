# Import the necessary modules and create the Flask app
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from xrf_explorer.server.database.database import init_app
from xrf_explorer.server.database.models import User  # Ensure models are imported
from xrf_explorer.server.database.models import UserRole

app: Flask = Flask(__name__, template_folder=Path('client/templates'), static_folder='client/dist')
CORS(app)
db = init_app(app)

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
    
    if not User.query.filter_by(role=UserRole.VIEWER).first():
        viewer_user = User(username='viewer', role=UserRole.VIEWER)
        viewer_user.set_password('viewerpassword')
        db.session.add(viewer_user)
        db.session.commit()
        print("Database initialized with default viewer user.")
    else:
        print("Viewer user already exists.")

from xrf_explorer.server.routes import *

# Login route
@app.route('/api/login', methods=['POST'])
def login():
    
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
        return jsonify({"success": True, "message": "Login successful", "role": user.role.name}), 200
    return jsonify({"success": False, "message": "Invalid username or password"}), 401


# All routes not matched in the server are forwarded to the client
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def catch_all(path):
    return send_from_directory(Path('client/dist'), path)

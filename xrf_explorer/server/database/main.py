from flask import Flask
from database import init_app
from models import User  # Ensure models are imported

app: Flask = Flask(__name__)
db = init_app(app)

with app.app_context():
    db.create_all()  # Create database tables for our data models
    
    # Create a default admin user if none exist
    if not User.query.filter_by(role=0).first():
        admin_user = User(username='admin', role=0)
        admin_user.set_password('testpassword')  # Set a default password; should be changed after first login
        db.session.add(admin_user)
        db.session.commit()
        print("Database initialized with default admin user.")
    else:
        print("Admin user already exists.")
        
    # Test viewer user
    if not User.query.filter_by(role=1).first():
        viewer_user = User(username='viewer', role=1)
        viewer_user.set_password('viewerpassword')
        db.session.add(viewer_user)
        db.session.commit()
        print("Database initialized with default viewer user.")
    else:
        print("Viewer user already exists.")
        
if __name__ == '__main__':
    with app.app_context():
        print("Current users in the database:")
        users = User.query.all()
        for user in users:
            print(user)


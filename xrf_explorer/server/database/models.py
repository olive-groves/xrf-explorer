from werkzeug.security import generate_password_hash, check_password_hash
# from xrf_explorer.server.database.database import db
from database import db

class User(db.Model):
    """User model for authentication and role management."""

    # Define the columns of the database table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Integer, nullable=False) # 0 = admin, 1 = viewer, 2 = editor
    
    def set_password(self, password: str):
        """Generate and store the password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check the password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<ID: {self.id}, Username {self.username}, Role {self.role}>'

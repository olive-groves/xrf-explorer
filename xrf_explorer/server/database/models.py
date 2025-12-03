import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
from xrf_explorer.server.database.database import db
from enum import Enum
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.types import JSON
from sqlalchemy.orm.attributes import flag_modified

class UserRole(Enum):
    ADMIN = 0
    VIEWER = 1
    EDITOR = 2

class User(db.Model, flask_login.UserMixin):
    """User model for authentication and role management."""

    # Define the columns of the database table
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.VIEWER) # 0 = admin, 1 = viewer, 2 = editor
    projects: list[str] = db.Column(MutableList.as_mutable(JSON), nullable=False, default=list) # List of projects the user has access to

    def set_password(self, password: str):
        """Generate and store the password hash."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check the password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def isAdmin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def isEditor(self) -> bool:
        return self.role == UserRole.EDITOR or self.role == UserRole.ADMIN

    def checkProjectAccess(self, project) -> bool:
        return project in self.projects
    
    def giveProjectAccess(self, project):
        self.projects.append(project)
        flag_modified(self, "projects")
        db.session.commit()

    def revokeProjectAccess(self, project):
        self.projects.remove(project)
        flag_modified(self, "projects")
        db.session.commit()

    def getProjects(self):
        return self.projects

    def __repr__(self) -> str:
        return f'<ID: {self.id}, Username {self.username}, Role {self.role}>'
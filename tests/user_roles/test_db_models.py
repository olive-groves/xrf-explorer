from xrf_explorer.server.database.database import init_app
from flask import Flask
from xrf_explorer.server.database.models import User, UserRole
import pytest
from sqlalchemy import inspect
import uuid


class TestDBModels:
    
    @pytest.fixture(scope="class", autouse=True)
    def test_app(self):
        # Create an in-memory SQLite database for testing
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            db.create_all()
            yield app, db
            db.drop_all()
    
    # Create sample users for testing
    @pytest.fixture(scope="function")
    def sample_users(self):
        def uname(name: str) -> str:
            return f"{name}_{uuid.uuid4().hex[:6]}"
        
        user_admin = User(username=uname('admin'), password_hash='adminpass', role=UserRole.ADMIN)
        user_viewer = User(username=uname('viewer'), password_hash='viewerpass', role=UserRole.VIEWER)
        user_editor = User(username=uname('editor'), password_hash='editorpass', role=UserRole.EDITOR)
        return user_admin, user_viewer, user_editor
    
    # -------------------- Tests --------------------
        
    def test_userRoles_Enums(self):
        assert UserRole.ADMIN.value == 0
        assert UserRole.VIEWER.value == 1
        assert UserRole.EDITOR.value == 2
    
    def test_db_columns(self, test_app):
        _, db = test_app
        inspector = db.inspect(db.engine)
        columns = {column['name'] for column in inspector.get_columns('user')}
        expected_columns = {'id', 'username', 'password_hash', 'role', 'projects'}
        assert columns == expected_columns

    def test_user_creation(self, sample_users, test_app):
        user_admin, user_viewer, user_editor = sample_users
        _, db = test_app
        
        db.session.add_all([user_admin, user_viewer, user_editor])
        db.session.commit()
        
        for user in [user_admin, user_viewer, user_editor]:
            retrieved_user = User.query.filter_by(username=user.username).first()
            assert retrieved_user is not None
            assert retrieved_user.username == user.username
            assert retrieved_user.password_hash == user.password_hash
            assert retrieved_user.role == user.role
     
    def test_userRole_default(self, test_app):
        app, db = test_app
        
        with app.app_context():
            user_default = User(username='defaultuser', password_hash='defaultpass')
            db.session.add(user_default)
            db.session.commit()
            
            retrieved_user = User.query.filter_by(username='defaultuser').first()
            assert retrieved_user is not None
            assert retrieved_user.role == UserRole.VIEWER  # Default role should be VIEWER
        
    def test_user_creation_without_password(self, test_app):
        app, db = test_app
        
        with app.app_context():
            user_no_password = User(username='nopass', role=UserRole.VIEWER)
            with pytest.raises(ValueError) as excinfo:
                user_no_password.set_password(None)
                # Error should be raised when trying to add user without setting password
                db.session.add(user_no_password)
                db.session.commit()
                
            assert "Password cannot be empty" in str(excinfo.value)

    def test_set_and_check_password(self, test_app):
        app, db = test_app
        
        with app.app_context():
            user = User(username='testuser', role=UserRole.VIEWER)
            user.set_password('securepassword')
            db.session.add(user)
            db.session.commit()
            
            retrieved_user = User.query.filter_by(username='testuser').first()
            assert retrieved_user is not None
            assert retrieved_user.check_password('securepassword') is True
            assert retrieved_user.check_password('wrongpassword') is False
    
    def test_set_password_empty(self, test_app):
        app, _ = test_app
        
        with app.app_context():
            user1 = User(username='emptytest', role=UserRole.VIEWER)
            with pytest.raises(ValueError) as excinfo:
                user1.set_password('')
            assert "Password cannot be empty" in str(excinfo.value)
    
    def test_set_password_none(self, test_app):
        app, _ = test_app
        
        with app.app_context():
            user = User(username='nonetest', role=UserRole.VIEWER)
            with pytest.raises(ValueError) as excinfo:
                user.set_password(None)
            assert "Password cannot be empty" in str(excinfo.value)
    
    def test_userRole_isAdmin(self, sample_users):
        user_admin, user_viewer, user_editor = sample_users
        assert user_admin.isAdmin() is True
        assert user_viewer.isAdmin() is False
        assert user_editor.isAdmin() is False
    
    def test_userRole_isViewer(self, sample_users):
        user_admin, user_viewer, user_editor = sample_users
        assert user_admin.role != UserRole.VIEWER
        assert user_viewer.role == UserRole.VIEWER
        assert user_editor.role != UserRole.VIEWER
    
    def test_userRole_isEditor(self, sample_users):
        user_admin, user_viewer, user_editor = sample_users
        assert user_admin.isEditor() is True
        assert user_viewer.isEditor() is False
        assert user_editor.isEditor() is True
                
    def test__repr__(self, sample_users, test_app):
        app, db = test_app
        with app.app_context():
            # Ensure users are added to the session
            for user in sample_users:
                db.session.add(user)
            db.session.commit()
            
            for user in sample_users:
                expected_repr = f'<ID: {user.id}, Username {user.username}, Role {user.role}>'
                assert repr(user) == expected_repr
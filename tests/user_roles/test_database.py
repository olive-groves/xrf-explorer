import os
from xrf_explorer.server.database.database import init_app
from xrf_explorer.server.database import database

from flask import Flask

class TestDatabase:
    
    def test_database_file_exists(self):
        """Check if the database file is created in the expected location."""
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            modulo_dir = os.path.abspath(os.path.dirname(database.__file__))
            db_path = os.path.join(modulo_dir, 'xrf_explorer.db')
            
            assert os.path.isfile(db_path), f"Database file not found at {db_path}"
            
    def test_database_connection(self):
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            connection = db.engine.connect()
            assert connection.closed == False, "Database connection should be open"
            connection.close()
            assert connection.closed == True, "Database connection should be closed"
    
    def test_database_uri_configuration(self):
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            expected_uri_start = 'sqlite:///'
            actual_uri = app.config['SQLALCHEMY_DATABASE_URI']
            assert actual_uri.startswith(expected_uri_start), f"Database URI should start with {expected_uri_start}"
            
    def test_database_track_modifications_setting(self):
        app = Flask(__name__)
        db = init_app(app)
        with app.app_context():
            assert app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] == False, "SQLALCHEMY_TRACK_MODIFICATIONS should be set to False"
                
    
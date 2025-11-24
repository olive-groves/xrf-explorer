from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize the SQLAlchemy object
db = SQLAlchemy()

def init_app(app: Flask):
    """Initialize the database and attach it to the Flask app."""
    
    # Create the database file in the current directory
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'xrf_explorer.db')
    
    # Configure the Flask app for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    return db
import sqlite3
import os
from flask import current_app

def get_db_connection():
    """
    Establish a connection to the SQLite database.
    Supports running within or outside of the Flask application context.
    """
    try:
        db_path = current_app.config['DATABASE']
    except RuntimeError:
        # Fallback when running outside of Flask context
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'instance', 'database.db')
    
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

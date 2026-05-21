from flask import Flask
import sqlite3
import os

from app.routes.main import main_bp

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['DATABASE'] = os.path.join(os.getcwd(), 'instance', 'database.db')
app.register_blueprint(main_bp)

def init_db():
    """Initialize and seed the SQLite database."""
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db = sqlite3.connect(app.config['DATABASE'])
    with open('database/schema.sql', 'r', encoding='utf-8') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

# Initialize DB if it doesn't exist yet (works for both python app.py and flask run)
if not os.path.exists(app.config['DATABASE']):
    init_db()

if __name__ == '__main__':
    app.run(debug=True)

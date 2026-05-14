from flask import Flask, render_template
import sqlite3
import os

from app.routes.main import main_bp

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.register_blueprint(main_bp)
app.config['DATABASE'] = os.path.join(os.getcwd(), 'instance', 'database.db')

def init_db():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    db = sqlite3.connect(app.config['DATABASE'])
    with open('database/schema.sql', 'r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)

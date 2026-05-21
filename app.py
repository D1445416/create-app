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
    
    # Check if stations table is empty or has mock stations only
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM stations")
    count = cursor.fetchone()[0]
    db.close()
    
    if count < 50:
        print("Stations count is low. Attempting to seed real stations from TDX...")
        success = False
        try:
            from database.fetch_tdx_stations import fetch_and_seed_all
            success = fetch_and_seed_all()
        except Exception as e:
            print("Failed to run real stations seeding:", e)
            
        if not success:
            print("Falling back to local mock seeding...")
            db = sqlite3.connect(app.config['DATABASE'])
            cursor = db.cursor()
            seed_stations = [
                ('HUB_01', '市政府站轉乘樞紐', 24.1628, 120.6439, 'transfer'),
                ('HUB_02', '台中車站轉乘樞紐', 24.1373, 120.6856, 'transfer'),
                ('MRT_01', '市政府捷運站', 24.1628, 120.6439, 'mrt'),
                ('MRT_02', '水安宮捷運站', 24.1508, 120.6473, 'mrt'),
                ('MRT_03', '文心森林公園捷運站', 24.1437, 120.6444, 'mrt'),
                ('MRT_04', '豐樂公園捷運站', 24.1317, 120.6465, 'mrt'),
                ('BUS_01', '台中車站(台灣大道)', 24.1380, 120.6850, 'bus'),
                ('BUS_02', '科博館公車站', 24.1558, 120.6631, 'bus'),
                ('BUS_03', '秋紅谷公車站', 24.1663, 120.6375, 'bus'),
                ('BUS_04', '逢甲大學公車站', 24.1788, 120.6466, 'bus')
            ]
            cursor.executemany(
                "INSERT OR REPLACE INTO stations (station_id, station_name, lat, lon, transport_type) VALUES (?, ?, ?, ?, ?)",
                seed_stations
            )
            db.commit()
            db.close()


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)

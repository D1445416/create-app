import os
from flask import Flask, g
from app.routes import ALL_BLUEPRINTS

def create_app(test_config=None):
    """
    Flask 應用程式工廠。
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # 預設設定
    db_path = os.path.abspath(os.path.join(app.root_path, '../instance/database.db'))
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key'),
        DATABASE=os.environ.get('DATABASE', db_path),
    )

    if test_config is None:
        # 載入實例設定（如果有的話）
        app.config.from_pyfile('config.py', silent=True)
    else:
        # 載入測試設定
        app.config.from_mapping(test_config)

    # 確保 instance 目錄存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 註冊資料庫連線釋放機制
    @app.teardown_appcontext
    def close_db(e=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    # 註冊所有 Blueprints
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    return app

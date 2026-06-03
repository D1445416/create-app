import os
from flask import Flask
from dotenv import load_dotenv

# 載入 .env 檔案中的環境變數
load_dotenv()

def create_app(test_config=None):
    """
    Flask 應用程式工廠 (Application Factory)
    負責初始化 Flask App、載入設定、註冊路由與 CLI 命令。
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # 全域設定
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'taichung_transit_default_secret_key_12345'),
        DATABASE=os.path.join(app.instance_path, 'database.db'),
    )

    if test_config is not None:
        app.config.from_mapping(test_config)

    # 確保 SQLite 資料庫所在的 instance 目錄存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # 註冊控制器 Blueprint 路由
    from app.routes import views_bp
    app.register_blueprint(views_bp)

    # 提供 Flask 命令行工具以進行資料庫初始化： flask init-db
    @app.cli.command('init-db')
    def init_db_command():
        """重新初始化 SQLite 資料表 (會清空舊有資料)。"""
        from app.models import init_db, get_db_connection
        conn = get_db_connection(app.config['DATABASE'])
        init_db(conn)
        conn.close()
        print("資料庫初始化完成！")

    return app

def init_db():
    """
    供外部腳本 (如整合測試或部署工具) 直接呼叫初始化資料庫的函式。
    """
    from app.models import init_db as model_init, get_db_connection
    # 直接使用預設的 instance 資料庫路徑進行初始化
    conn = get_db_connection()
    model_init(conn)
    conn.close()

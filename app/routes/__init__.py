from app.routes.main import main_bp
from app.routes.transit import transit_bp
from app.routes.auth import auth_bp

# 匯出所有的 Blueprint 方便一併註冊
ALL_BLUEPRINTS = [
    main_bp,
    transit_bp,
    auth_bp
]

from app.routes.main import main_bp
from app.routes.transit import transit_bp
from app.routes.auth import auth_bp
from app.routes.views import views_bp
from app.routes.f03_routing import f03_bp

# 匯出所有的 Blueprint 方便一併註冊
ALL_BLUEPRINTS = [
    main_bp,
    transit_bp,
    auth_bp,
    views_bp,
    f03_bp
]

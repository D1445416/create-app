# 路由套件初始化，導出 Blueprint 供 app.py 註冊使用
# 檔案路徑: app/routes/__init__.py

from .views import views_bp

__all__ = ['views_bp']

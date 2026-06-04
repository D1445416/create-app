# 服務模組初始化，導出 tdx_service 單例
# 檔案路徑: app/services/__init__.py

from .tdx_api import tdx_service

__all__ = ['tdx_service']

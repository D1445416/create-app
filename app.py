import os
from app import create_app

# 建立 Flask 應用程式實例
app = create_app()

if __name__ == '__main__':
    # 支援以 python app.py 啟動本地偵錯伺服器
    port = int(os.getenv('PORT', 5000))
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    
    print(f"==================================================")
    print(f" 台中大眾運輸站點擁擠度系統本地偵錯伺服器啟動中...")
    print(f" 網址: http://127.0.0.1:{port}")
    print(f"==================================================")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

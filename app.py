import os
from dotenv import load_dotenv
from app import create_app

# 載入 .env 檔案的環境變數
load_dotenv()

app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    
    app.run(host=host, port=port, debug=debug)

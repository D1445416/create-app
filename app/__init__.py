from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Load config from environment or default
    app.config['SECRET_KEY'] = 'dev_secret_key'

    # Register blueprints
    from app.routes.f03_routing import f03_bp
    app.register_blueprint(f03_bp, url_prefix='/f03')

    @app.route('/')
    def index():
        return '歡迎來到交通資訊整合平台！請前往 <a href="/f03/planner">多運具轉乘路徑演算模組 (F-03)</a>'

    return app

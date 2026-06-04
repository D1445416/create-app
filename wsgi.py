import importlib.util
import os

# Resolve collision between app/ folder and app.py in root for production gunicorn
spec = importlib.util.spec_from_file_location("app_root", os.path.join(os.path.dirname(__file__), "app.py"))
app_root = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_root)
app = app_root.app

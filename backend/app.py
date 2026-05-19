from __future__ import annotations

import json
import os
from typing import Any

from flask import Flask, send_from_directory
from flask_cors import CORS

try:
    from .config import BASE_DIR, FAVORITES_FILE, UPLOADS_DIR, WARDROBE_FILE
    from .routes.chat import chat_bp
    from .routes.meta import meta_bp
    from .routes.products import products_bp
    from .routes.recommend import recommend_bp
    from .routes.wardrobe import wardrobe_bp
except ImportError:
    from backend.config import BASE_DIR, FAVORITES_FILE, UPLOADS_DIR, WARDROBE_FILE
    from backend.routes.chat import chat_bp
    from backend.routes.meta import meta_bp
    from backend.routes.products import products_bp
    from backend.routes.recommend import recommend_bp
    from backend.routes.wardrobe import wardrobe_bp

app = Flask(__name__)
CORS(app)

FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

def ensure_data_files() -> None:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    if not os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)
    if not os.path.exists(WARDROBE_FILE):
        with open(WARDROBE_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)

@app.route("/")
def index() -> Any:
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/css/<path:path>")
def serve_css(path: str) -> Any:
    return send_from_directory(os.path.join(FRONTEND_DIR, "css"), path)

@app.route("/js/<path:path>")
def serve_js(path: str) -> Any:
    return send_from_directory(os.path.join(FRONTEND_DIR, "js"), path)

@app.route("/<path:path>")
def serve_frontend_static(path: str) -> Any:
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/uploads/<filename>")
def uploads(filename: str) -> Any:
    return send_from_directory(UPLOADS_DIR, filename)

# Register blueprints (must be before the catch-all frontend route)
app.register_blueprint(products_bp)
app.register_blueprint(wardrobe_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(meta_bp)

ensure_data_files()

if __name__ == "__main__":
    app.run(debug=True)

from __future__ import annotations

from flask import Flask, send_from_directory
from flask_cors import CORS
import os

from .config import UPLOADS_DIR
from .routes.chat import chat_bp
from .routes.meta import meta_bp
from .routes.products import products_bp
from .routes.recommend import recommend_bp
from .routes.wardrobe import wardrobe_bp
from backend.utils.data_loader import load_json, save_json

app = Flask(__name__)
CORS(app)

def ensure_data_files() -> None:
    from backend.config import FAVORITES_FILE, WARDROBE_FILE, UPLOADS_DIR
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    if not os.path.exists(FAVORITES_FILE):
        with open(FAVORITES_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)
    if not os.path.exists(WARDROBE_FILE):
        with open(WARDROBE_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, indent=2)

@app.route("/")
def home() -> str:
    return "AI Outfit Recommendation API is running."

@app.route("/uploads/<filename>")
def uploads(filename: str) -> Any:
    return send_from_directory(UPLOADS_DIR, filename)

# Register blueprints
app.register_blueprint(products_bp)
app.register_blueprint(wardrobe_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(meta_bp)

ensure_data_files()

if __name__ == "__main__":
    app.run(debug=True)

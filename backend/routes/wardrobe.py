import os
import uuid
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from ..config import ALLOWED_IMAGE_EXTENSIONS, UPLOADS_DIR
from ..services.detection import detect_clothing
from ..services.recommendations import load_wardrobe, generate_wardrobe_outfits
from ..utils.data_loader import save_json
from ..utils.validators import parse_budget

wardrobe_bp = Blueprint("wardrobe", __name__)

@wardrobe_bp.route("/wardrobe", methods=["GET"])
def wardrobe() -> Any:
    return jsonify(load_wardrobe())

@wardrobe_bp.route("/wardrobe", methods=["POST"])
def add_wardrobe_item() -> Any:
    from backend.config import WARDROBE_FILE
    payload = request.get_json(silent=True) or {}
    wardrobe_items = load_wardrobe()
    item = {
        "id": f"wardrobe-{len(wardrobe_items) + 1}",
        "name": payload.get("name", ""),
        "category": payload.get("category", ""),
        "color": payload.get("color", "unknown"),
        "style": payload.get("style", "casual"),
        "occasion": payload.get("occasion", "casual"),
        "image": payload.get("image", ""),
    }

    if not item["name"] or item["category"] not in {"top", "bottom", "shoes", "accessory"}:
        return jsonify({"error": "Valid name and category are required"}), 400

    wardrobe_items.append(item)
    save_json(WARDROBE_FILE, wardrobe_items)
    return jsonify(item), 201

@wardrobe_bp.route("/wardrobe/upload", methods=["POST"])
def upload_wardrobe_image() -> Any:
    image = request.files.get("image")
    if image is None or not image.filename:
        return jsonify({"error": "Image file is required"}), 400

    extension = os.path.splitext(image.filename)[1].lower() or ".jpg"
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Only JPG, JPEG, PNG, and WEBP images are supported"}), 400
    filename = f"{uuid.uuid4().hex}{extension}"
    saved_path = os.path.join(UPLOADS_DIR, filename)
    image.save(saved_path)
    inferred = detect_clothing(saved_path)

    return jsonify({"image": f"/uploads/{filename}", "analysis": inferred})

@wardrobe_bp.route("/wardrobe/<item_id>", methods=["DELETE"])
def delete_wardrobe_item(item_id: str) -> Any:
    from backend.config import WARDROBE_FILE
    wardrobe_items = load_wardrobe()
    updated = [item for item in wardrobe_items if item.get("id") != item_id]
    if len(updated) == len(wardrobe_items):
        return jsonify({"error": "Wardrobe item not found"}), 404
    save_json(WARDROBE_FILE, updated)
    return jsonify({"deleted": item_id})

@wardrobe_bp.route("/wardrobe/generate", methods=["POST"])
def wardrobe_generate() -> Any:
    payload = request.get_json(silent=True) or {}
    occasion = str(payload.get("occasion", "casual")).strip().lower()
    style = str(payload.get("style", "casual")).strip().lower()
    outfits = generate_wardrobe_outfits(occasion, style)
    return jsonify(
        {
            "query": {"occasion": occasion, "style": style},
            "outfits": outfits,
            "count": len(outfits),
        }
    )
from typing import Any

from flask import Blueprint, jsonify, request

from ..config import DEFAULT_BUDGET, DEFAULT_OCCASION, DEFAULT_STYLE, FAVORITES_FILE

from ..services.recommendations import load_favorites, recommend_outfits

from ..utils.data_loader import save_json

from ..utils.validators import parse_budget

recommend_bp = Blueprint("recommend", __name__)

@recommend_bp.route("/recommend", methods=["POST"])
def recommend() -> Any:
    payload = request.get_json(silent=True) or {}
    occasion = str(payload.get("occasion", DEFAULT_OCCASION)).strip().lower()
    style = str(payload.get("style", DEFAULT_STYLE)).strip().lower()
    budget = parse_budget(payload.get("budget", DEFAULT_BUDGET))

    outfits = recommend_outfits(occasion, style, budget)
    return jsonify(
        {
            "query": {
                "occasion": occasion,
                "style": style,
                "budget": budget,
            },
            "outfits": outfits,
            "summary": {
                "count": len(outfits),
                "trending_note": "Trend score is blended into ranking so modern pieces surface first.",
                "designer_note": "Local designers receive a small boost when they still fit the occasion and budget.",
            },
        }
    )

@recommend_bp.route("/favorites", methods=["GET"])
def favorites() -> Any:
    return jsonify(load_favorites())

@recommend_bp.route("/favorites", methods=["POST"])
def add_favorite() -> Any:
    payload = request.get_json(silent=True) or {}
    outfit = payload.get("outfit")
    if not isinstance(outfit, dict):
        return jsonify({"error": "Outfit payload is required"}), 400

    favorites_data = load_favorites()
    favorite_name = str(payload.get("name", "Saved Outfit")).strip() or "Saved Outfit"
    record = {
        "id": f"fav-{len(favorites_data) + 1}",
        "name": favorite_name,
        "outfit": outfit,
    }
    favorites_data.append(record)
    save_json(FAVORITES_FILE, favorites_data)
    return jsonify(record), 201

@recommend_bp.route("/favorites/<favorite_id>", methods=["DELETE"])
def delete_favorite(favorite_id: str) -> Any:
    favorites_data = load_favorites()
    updated = [item for item in favorites_data if item.get("id") != favorite_id]
    if len(updated) == len(favorites_data):
        return jsonify({"error": "Favorite not found"}), 404
    save_json(FAVORITES_FILE, updated)
    return jsonify({"deleted": favorite_id})

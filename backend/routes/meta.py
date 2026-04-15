from flask import Blueprint, jsonify

from backend.config import DEFAULT_BUDGET

meta_bp = Blueprint("meta", __name__)

@meta_bp.route("/meta", methods=["GET"])
def meta() -> Any:
    return jsonify(
        {
            "occasions": ["wedding", "casual", "party", "college", "formal"],
            "styles": ["minimal", "streetwear", "ethnic", "classic", "chic", "smart-casual"],
            "budgets": [2000, 5000, 10000],
        }
    )
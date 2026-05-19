from typing import Any

from flask import Blueprint, jsonify

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

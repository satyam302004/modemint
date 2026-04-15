from flask import Blueprint, jsonify

from ..services.recommendations import load_products, load_trends

products_bp = Blueprint("products", __name__)

@products_bp.route("/products", methods=["GET"])
def products() -> Any:
    catalog = load_products()
    return jsonify(catalog)

@products_bp.route("/trends", methods=["GET"])
def trends() -> Any:
    return jsonify(load_trends())
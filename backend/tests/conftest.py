import json
import os
import tempfile
import shutil

import pytest

from backend.app import app as _app


@pytest.fixture(autouse=True)
def temp_data_files(monkeypatch):
    """Replace all JSON file paths with temp files so tests don't pollute real data."""
    tmpdir = tempfile.mkdtemp()
    real_data = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

    # Copy products.json and trends.json from real data (read-only reference)
    for fname in ["products.json", "trends.json"]:
        src = os.path.join(real_data, fname)
        dst = os.path.join(tmpdir, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)

    # Empty mutable data files
    for fname in ["favorites.json", "wardrobe.json"]:
        with open(os.path.join(tmpdir, fname), "w", encoding="utf-8") as f:
            json.dump([], f)

    # Monkeypatch config file paths
    monkeypatch.setattr("backend.config.DATA_DIR", tmpdir)
    monkeypatch.setattr("backend.config.PRODUCTS_FILE", os.path.join(tmpdir, "products.json"))
    monkeypatch.setattr("backend.config.TRENDS_FILE", os.path.join(tmpdir, "trends.json"))
    monkeypatch.setattr("backend.config.FAVORITES_FILE", os.path.join(tmpdir, "favorites.json"))
    monkeypatch.setattr("backend.config.WARDROBE_FILE", os.path.join(tmpdir, "wardrobe.json"))

    # Also monkeypatch module-level imports that captured the old paths
    monkeypatch.setattr("backend.services.recommendations.PRODUCTS_FILE", os.path.join(tmpdir, "products.json"))
    monkeypatch.setattr("backend.services.recommendations.TRENDS_FILE", os.path.join(tmpdir, "trends.json"))
    monkeypatch.setattr("backend.services.recommendations.FAVORITES_FILE", os.path.join(tmpdir, "favorites.json"))
    monkeypatch.setattr("backend.services.recommendations.WARDROBE_FILE", os.path.join(tmpdir, "wardrobe.json"))
    monkeypatch.setattr("backend.routes.recommend.FAVORITES_FILE", os.path.join(tmpdir, "favorites.json"))


    yield

    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def app():
    _app.config["TESTING"] = True
    _app.config["SERVER_NAME"] = "localhost"
    yield _app


@pytest.fixture
def client(app):
    with app.test_client() as c:
        yield c


@pytest.fixture
def temp_json_file():
    path = os.path.join(tempfile.gettempdir(), f"test_{os.urandom(4).hex()}.json")
    def _create(data):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path
    yield _create
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_products():
    return [
        {
            "id": "p1", "name": "White Shirt", "category": "top",
            "price": 1200, "brand": "BrandA", "designer_type": "local",
            "occasions": ["casual", "formal"], "styles": ["minimal", "classic"],
            "trend_score": 7.5, "buy_link": "", "image": "", "description": "",
        },
        {
            "id": "p2", "name": "Blue Jeans", "category": "bottom",
            "price": 1500, "brand": "BrandB", "designer_type": "local",
            "occasions": ["casual"], "styles": ["minimal"],
            "trend_score": 6.0, "buy_link": "", "image": "", "description": "",
        },
        {
            "id": "p3", "name": "Canvas Shoes", "category": "shoes",
            "price": 800, "brand": "BrandC", "designer_type": "local",
            "occasions": ["casual", "college"], "styles": ["minimal", "streetwear"],
            "trend_score": 5.0, "buy_link": "", "image": "", "description": "",
        },
        {
            "id": "p4", "name": "Watch", "category": "accessory",
            "price": 500, "brand": "BrandD", "designer_type": "local",
            "occasions": ["casual", "formal"], "styles": ["minimal", "classic"],
            "trend_score": 3.0, "buy_link": "", "image": "", "description": "",
        },
        {
            "id": "p5", "name": "Black Blazer", "category": "top",
            "price": 3000, "brand": "BrandE", "designer_type": "local",
            "occasions": ["formal"], "styles": ["classic"],
            "trend_score": 8.0, "buy_link": "", "image": "", "description": "",
        },
    ]

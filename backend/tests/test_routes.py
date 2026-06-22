import json
import pytest


# ── GET /meta ──────────────────────────────────────────────────────────────

class TestMeta:
    def test_returns_200(self, client):
        r = client.get("/meta")
        assert r.status_code == 200
        data = r.get_json()
        assert "occasions" in data
        assert "styles" in data
        assert "budgets" in data
        assert isinstance(data["occasions"], list)
        assert len(data["occasions"]) >= 4

    def test_includes_expected_values(self, client):
        r = client.get("/meta")
        data = r.get_json()
        assert "wedding" in data["occasions"]
        assert "streetwear" in data["styles"]
        assert 5000 in data["budgets"]


# ── GET /products ──────────────────────────────────────────────────────────

class TestProducts:
    def test_returns_200(self, client):
        r = client.get("/products")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_products_have_required_keys(self, client):
        r = client.get("/products")
        data = r.get_json()
        required = {"id", "name", "category", "price", "brand", "occasions", "styles", "trend_score"}
        for product in data[:5]:
            assert required.issubset(product.keys()), f"Missing keys in {product['id']}"


# ── GET /trends ────────────────────────────────────────────────────────────

class TestTrends:
    def test_returns_200(self, client):
        r = client.get("/trends")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)

    def test_trends_have_required_keys(self, client):
        r = client.get("/trends")
        data = r.get_json()
        if data:
            required = {"id", "keyword", "score", "region", "season"}
            assert required.issubset(data[0].keys())


# ── POST /recommend ────────────────────────────────────────────────────────

class TestRecommend:
    def test_valid_request_returns_200(self, client):
        r = client.post("/recommend", json={
            "occasion": "casual",
            "style": "minimal",
            "budget": 5000,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert "outfits" in data
        assert "summary" in data
        assert "query" in data

    def test_outfits_are_scored(self, client):
        r = client.post("/recommend", json={
            "occasion": "casual",
            "style": "minimal",
            "budget": 10000,
        })
        data = r.get_json()
        for outfit in data["outfits"]:
            assert "score" in outfit
            assert "items" in outfit
            assert "total_price" in outfit
            assert "trend_score" in outfit
            assert "reasons" in outfit

    def test_missing_body_uses_defaults(self, client):
        r = client.post("/recommend", json={})
        assert r.status_code == 200

    def test_empty_body_uses_defaults(self, client):
        r = client.post("/recommend", data="{}", content_type="application/json")
        assert r.status_code == 200

    def test_very_low_budget_returns_empty(self, client):
        r = client.post("/recommend", json={
            "occasion": "casual",
            "style": "minimal",
            "budget": 1,
        })
        data = r.get_json()
        assert data["outfits"] == []

    def test_invalid_occasion_returns_empty(self, client):
        r = client.post("/recommend", json={
            "occasion": "nonexistent_occasion_xyz",
            "style": "minimal",
            "budget": 5000,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["outfits"] == []

    def test_outfits_sorted_by_score(self, client):
        r = client.post("/recommend", json={
            "occasion": "college",
            "style": "streetwear",
            "budget": 3000,
        })
        data = r.get_json()
        scores = [o["score"] for o in data["outfits"]]
        assert scores == sorted(scores, reverse=True)

    def test_outfits_limited_to_6(self, client):
        r = client.post("/recommend", json={
            "occasion": "casual",
            "style": "minimal",
            "budget": 50000,
        })
        data = r.get_json()
        assert len(data["outfits"]) <= 6


# ── GET/POST/DELETE /favorites ─────────────────────────────────────────────

class TestFavorites:
    def test_get_empty(self, client):
        r = client.get("/favorites")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_create_and_delete_cycle(self, client):
        payload = {
            "name": "Test Favorite",
            "outfit": {
                "items": {"top": {"name": "Shirt"}},
                "total_price": 500,
                "score": 5.0,
                "trend_score": 5.0,
                "reasons": ["test"],
            },
        }
        r = client.post("/favorites", json=payload)
        assert r.status_code == 201
        created = r.get_json()
        assert created["name"] == "Test Favorite"
        fav_id = created["id"]

        r = client.get("/favorites")
        assert len(r.get_json()) >= 1

        r = client.delete(f"/favorites/{fav_id}")
        assert r.status_code == 200

        r = client.get("/favorites")
        assert fav_id not in [f["id"] for f in r.get_json()]

    def test_create_without_outfit_returns_400(self, client):
        r = client.post("/favorites", json={"name": "Bad"})
        assert r.status_code == 400

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/favorites/fav-nonexistent")
        assert r.status_code == 404

    def test_create_returns_unique_id(self, client):
        r1 = client.post("/favorites", json={
            "name": "A", "outfit": {"items": {}, "total_price": 0, "score": 0, "trend_score": 0, "reasons": []},
        })
        r2 = client.post("/favorites", json={
            "name": "B", "outfit": {"items": {}, "total_price": 0, "score": 0, "trend_score": 0, "reasons": []},
        })
        assert r1.get_json()["id"] != r2.get_json()["id"]


# ── GET/POST/DELETE /wardrobe ──────────────────────────────────────────────

class TestWardrobe:
    def test_get_empty(self, client):
        r = client.get("/wardrobe")
        assert r.status_code == 200
        assert r.get_json() == []

    def test_create_item(self, client):
        r = client.post("/wardrobe", json={
            "name": "Test Shirt",
            "category": "top",
            "color": "white",
            "style": "casual",
            "occasion": "casual",
        })
        assert r.status_code == 201
        item = r.get_json()
        assert item["name"] == "Test Shirt"
        assert item["category"] == "top"
        assert "id" in item

    def test_create_missing_name_returns_400(self, client):
        r = client.post("/wardrobe", json={"category": "top"})
        assert r.status_code == 400

    def test_create_invalid_category_returns_400(self, client):
        r = client.post("/wardrobe", json={"name": "X", "category": "invalid"})
        assert r.status_code == 400

    def test_delete_item(self, client):
        r = client.post("/wardrobe", json={
            "name": "To Delete", "category": "top",
        })
        item_id = r.get_json()["id"]

        r = client.delete(f"/wardrobe/{item_id}")
        assert r.status_code == 200

        r = client.get("/wardrobe")
        assert item_id not in [i["id"] for i in r.get_json()]

    def test_delete_nonexistent_returns_404(self, client):
        r = client.delete("/wardrobe/nonexistent-id")
        assert r.status_code == 404


# ── POST /wardrobe/generate ────────────────────────────────────────────────

class TestWardrobeGenerate:
    def test_empty_wardrobe_returns_empty(self, client):
        r = client.post("/wardrobe/generate", json={
            "occasion": "casual",
            "style": "casual",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["outfits"] == []

    def test_generate_with_items(self, client):
        client.post("/wardrobe", json={
            "name": "Tee", "category": "top", "color": "w", "style": "casual", "occasion": "casual",
        })
        client.post("/wardrobe", json={
            "name": "Jeans", "category": "bottom", "color": "b", "style": "casual", "occasion": "casual",
        })
        client.post("/wardrobe", json={
            "name": "Sneakers", "category": "shoes", "color": "w", "style": "casual", "occasion": "casual",
        })
        r = client.post("/wardrobe/generate", json={
            "occasion": "casual",
            "style": "casual",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["outfits"]) >= 1


# ── POST /chat ─────────────────────────────────────────────────────────────

class TestChat:
    def test_greeting_returns_intro(self, client):
        r = client.post("/chat", json={"message": "hello"})
        assert r.status_code == 200
        data = r.get_json()
        assert "response" in data
        # Greeting should not contain raw outfit structure — should be a help intro
        assert data["response"] is not None
        assert len(data["response"]) > 10

    def test_fashion_query_returns_outfit(self, client):
        r = client.post("/chat", json={
            "message": "what should I wear casually under 5000",
        })
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["response"]) > 50

    def test_empty_message_returns_400(self, client):
        r = client.post("/chat", json={"message": ""})
        assert r.status_code == 400

    def test_missing_message_returns_400(self, client):
        r = client.post("/chat", json={})
        assert r.status_code == 400

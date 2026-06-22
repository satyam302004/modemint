import pytest

from backend.services.recommendations import (
    normalize_product,
    normalize_wardrobe_item,
    filter_products,
    score_outfit,
    score_wardrobe_outfit,
    recommend_outfits_with_limit,
    generate_wardrobe_outfits,
    compute_trend_boost,
    build_reasons,
    REQUIRED_CATEGORIES,
    WARDROBE_REQUIRED_CATEGORIES,
)


# ── normalize_product ─────────────────────────────────────────────────────

class TestNormalizeProduct:
    def test_typical(self):
        p = normalize_product({
            "id": "x1", "name": "Shirt", "category": "top",
            "price": 1200, "brand": "B", "designer_type": "local",
            "occasions": ["casual"], "styles": ["minimal"],
            "trend_score": 7.5, "buy_link": "", "image": "", "description": "desc",
        })
        assert p["id"] == "x1"
        assert p["price"] == 1200
        assert p["trend_score"] == 7.5
        assert p["occasions"] == ["casual"]

    def test_missing_keys_default(self):
        p = normalize_product({})
        assert p["id"] == ""
        assert p["name"] == ""
        assert p["price"] == 0
        assert p["trend_score"] == 0.0
        assert p["occasions"] == []
        assert p["styles"] == []

    def test_whitespace_stripped(self):
        p = normalize_product({"name": "  Shirt  ", "id": "  abc  "})
        assert p["name"] == "Shirt"
        assert p["id"] == "abc"


# ── filter_products ────────────────────────────────────────────────────────

class TestFilterProducts:
    def test_filters_by_occasion(self, sample_products):
        result = filter_products(sample_products, "formal", "minimal", 5000)
        assert len(result["top"]) == 1  # White Shirt (formal + minimal); Black Blazer is "classic" not "minimal"
        assert len(result["bottom"]) == 0

    def test_filters_by_style(self, sample_products):
        result = filter_products(sample_products, "casual", "streetwear", 5000)
        assert any(p["name"] == "Canvas Shoes" for p in result["shoes"])
        assert all(p["name"] != "White Shirt" for p in result["top"])

    def test_filters_by_budget(self, sample_products):
        result = filter_products(sample_products, "casual", "minimal", 1000)
        assert len(result["top"]) == 0   # White Shirt (1200) > 1000 → excluded
        assert len(result["shoes"]) == 1  # Canvas Shoes (800) ≤ 1000

    def test_empty_category_returns_empty(self):
        result = filter_products([], "casual", "minimal", 5000)
        for cat in REQUIRED_CATEGORIES:
            assert result[cat] == []

    def test_versatile_style_matches_any(self, sample_products):
        versatile = [{
            "id": "v1", "name": "Versatile Item", "category": "top",
            "price": 500, "brand": "B", "designer_type": "local",
            "occasions": ["casual"], "styles": ["versatile"],
            "trend_score": 5.0, "buy_link": "", "image": "", "description": "",
        }]
        result = filter_products(versatile, "casual", "streetwear", 5000)
        assert len(result["top"]) == 1


# ── score_outfit ───────────────────────────────────────────────────────────

class TestScoreOutfit:
    def test_basic_scoring(self, sample_products):
        by_id = {p["id"]: p for p in sample_products}
        items = {
            "top": by_id["p1"], "bottom": by_id["p2"],
            "shoes": by_id["p3"], "accessory": by_id["p4"],
        }
        result = score_outfit(items, "casual", "minimal", 5000)
        assert result["score"] > 0
        assert result["total_price"] == 1200 + 1500 + 800 + 500
        assert result["trend_score"] > 0
        assert len(result["reasons"]) > 0

    def test_empty_items_raises_zero_division(self):
        with pytest.raises(ZeroDivisionError):
            score_outfit({}, "casual", "minimal", 5000)

    def test_missing_trend_score_key_raises_keyerror(self):
        items = {
            "top": {"price": 500, "designer_type": "local", "styles": ["minimal"], "occasions": ["casual"]},
            "bottom": {"price": 500, "designer_type": "local", "styles": ["minimal"], "occasions": ["casual"]},
            "shoes": {"price": 500, "designer_type": "local", "styles": ["minimal"], "occasions": ["casual"]},
            "accessory": {"price": 500, "designer_type": "local", "styles": ["minimal"], "occasions": ["casual"]},
        }
        with pytest.raises(KeyError):
            score_outfit(items, "casual", "minimal", 5000)

    def test_budget_bonus_max(self, sample_products):
        by_id = {p["id"]: p for p in sample_products}
        items = {
            "top": by_id["p1"], "bottom": by_id["p2"],
            "shoes": by_id["p3"], "accessory": by_id["p4"],
        }
        result = score_outfit(items, "casual", "minimal", 100000)
        assert result["score"] > 0


# ── score_wardrobe_outfit ──────────────────────────────────────────────────

class TestScoreWardrobeOutfit:
    def test_basic(self):
        items = {
            "top": {"style": "casual", "occasion": "casual", "color": "white", "category": "top"},
            "bottom": {"style": "casual", "occasion": "versatile", "color": "blue", "category": "bottom"},
            "shoes": {"style": "streetwear", "occasion": "casual", "color": "white", "category": "shoes"},
        }
        result = score_wardrobe_outfit(items, "casual", "casual")
        assert result["score"] >= 5.0
        assert len(result["reasons"]) > 0

    def test_accessory_bonus(self):
        items = {
            "top": {"style": "casual", "occasion": "casual", "color": "white", "category": "top"},
            "bottom": {"style": "casual", "occasion": "casual", "color": "blue", "category": "bottom"},
            "shoes": {"style": "casual", "occasion": "casual", "color": "white", "category": "shoes"},
            "accessory": {"style": "casual", "occasion": "casual", "color": "black", "category": "accessory"},
        }
        result = score_wardrobe_outfit(items, "casual", "casual")
        assert result["score"] > 6.0


# ── recommend_outfits_with_limit ───────────────────────────────────────────

class TestRecommendOutfits:
    def test_returns_list(self, monkeypatch, sample_products):
        monkeypatch.setattr("backend.services.recommendations.load_products", lambda: sample_products)
        outfits = recommend_outfits_with_limit("casual", "minimal", 5000, limit=6)
        assert isinstance(outfits, list)
        assert len(outfits) <= 6

    def test_limit_respected(self, monkeypatch, sample_products):
        monkeypatch.setattr("backend.services.recommendations.load_products", lambda: sample_products)
        outfits = recommend_outfits_with_limit("casual", "minimal", 5000, limit=2)
        assert len(outfits) <= 2

    def test_empty_when_category_missing(self, monkeypatch, sample_products):
        # Request formal + streetwear → no bottom matches
        monkeypatch.setattr("backend.services.recommendations.load_products", lambda: sample_products)
        outfits = recommend_outfits_with_limit("formal", "streetwear", 5000, limit=6)
        assert outfits == []

    def test_empty_products(self, monkeypatch):
        monkeypatch.setattr("backend.services.recommendations.load_products", lambda: [])
        outfits = recommend_outfits_with_limit("casual", "minimal", 5000, limit=6)
        assert outfits == []


# ── generate_wardrobe_outfits ──────────────────────────────────────────────

class TestGenerateWardrobeOutfits:
    def test_empty_wardrobe(self, monkeypatch):
        monkeypatch.setattr("backend.services.recommendations.load_wardrobe", lambda: [])
        outfits = generate_wardrobe_outfits("casual", "casual")
        assert outfits == []

    def test_missing_category(self, monkeypatch):
        monkeypatch.setattr("backend.services.recommendations.load_wardrobe", lambda: [
            {"id": "w1", "name": "Shirt", "category": "top", "color": "w", "style": "casual", "occasion": "casual", "image": ""},
            {"id": "w2", "name": "Jeans", "category": "bottom", "color": "b", "style": "casual", "occasion": "casual", "image": ""},
        ])
        outfits = generate_wardrobe_outfits("casual", "casual")
        assert outfits == []

    def test_full_wardrobe(self, monkeypatch):
        monkeypatch.setattr("backend.services.recommendations.load_wardrobe", lambda: [
            {"id": "w1", "name": "Tee", "category": "top", "color": "white", "style": "casual", "occasion": "casual", "image": ""},
            {"id": "w2", "name": "Jeans", "category": "bottom", "color": "blue", "style": "casual", "occasion": "casual", "image": ""},
            {"id": "w3", "name": "Sneakers", "category": "shoes", "color": "white", "style": "casual", "occasion": "casual", "image": ""},
        ])
        outfits = generate_wardrobe_outfits("casual", "casual")
        assert len(outfits) >= 1


# ── compute_trend_boost ───────────────────────────────────────────────────

class TestComputeTrendBoost:
    def test_no_trends(self, monkeypatch, sample_products):
        monkeypatch.setattr("backend.services.recommendations.load_trends", lambda: [])
        by_id = {p["id"]: p for p in sample_products}
        items = {"top": by_id["p1"], "bottom": by_id["p2"], "shoes": by_id["p3"], "accessory": by_id["p4"]}
        result = compute_trend_boost(items, "casual", "minimal")
        assert result["trend_boost"] == 0.0
        assert result["trend_keywords"] == []


# ── build_reasons ──────────────────────────────────────────────────────────

class TestBuildReasons:
    def test_basic(self, sample_products):
        by_id = {p["id"]: p for p in sample_products}
        outfit = {
            "items": {"top": by_id["p1"]},
            "total_price": 1200,
            "trend_score": 7.5,
            "trend_keywords": ["Sustainable"],
        }
        reasons = build_reasons(outfit, "casual", "minimal", 5000)
        assert len(reasons) >= 2
        assert any("casual" in r for r in reasons)
        assert any("budget" in r for r in reasons or [])

    def test_under_budget_triggers_cheap_reason(self):
        outfit = {"items": {}, "total_price": 100, "trend_score": 5.0, "trend_keywords": []}
        reasons = build_reasons(outfit, "casual", "minimal", 1000)
        assert any("under budget" in r.lower() for r in reasons)

import pytest

from backend.services.openai_service import (
    detect_fashion_intent,
    extract_budget_from_text,
    extract_choice,
    extract_choice_from_aliases,
    build_chat_request_profile,
    build_local_chat_response,
)


# ── detect_fashion_intent ──────────────────────────────────────────────────

class TestDetectFashionIntent:
    def test_greeting_returns_false(self):
        assert detect_fashion_intent("hello") is False
        assert detect_fashion_intent("hi there") is False
        assert detect_fashion_intent("hey how are you") is False

    def test_fashion_queries_return_true(self):
        assert detect_fashion_intent("what should I wear") is True
        assert detect_fashion_intent("give me an outfit") is True
        assert detect_fashion_intent("recommend a style") is True
        assert detect_fashion_intent("I need a shirt") is True
        assert detect_fashion_intent("what is trending") is True

    def test_edge_cases(self):
        assert detect_fashion_intent("") is False
        assert detect_fashion_intent("   ") is False
        assert detect_fashion_intent("how is the weather") is False
        assert detect_fashion_intent("tell me a joke") is False


# ── extract_budget_from_text ───────────────────────────────────────────────

class TestExtractBudget:
    def test_explicit_budget(self):
        assert extract_budget_from_text("under 3000") == 3000
        assert extract_budget_from_text("budget 5000") == 5000
        assert extract_budget_from_text("around 2000 rupees") == 2000

    def test_no_number_returns_default(self):
        from backend.config import DEFAULT_BUDGET
        assert extract_budget_from_text("hello") == DEFAULT_BUDGET
        assert extract_budget_from_text("no numbers here") == DEFAULT_BUDGET

    def test_first_number_extracted(self):
        assert extract_budget_from_text("I have 1000 and need 500") == 1000
        assert extract_budget_from_text("give me 2 shirts under 3000") == 3000

    def test_low_number_has_minimum(self):
        assert extract_budget_from_text("budget 100") == 500


# ── extract_choice ─────────────────────────────────────────────────────────

class TestExtractChoice:
    def test_exact_match(self):
        assert extract_choice("casual look", {"casual", "formal"}, "formal") == "casual"

    def test_no_match_returns_default(self):
        assert extract_choice("random text", {"casual", "formal"}, "formal") == "formal"

    def test_substring_matches(self):
        assert extract_choice("casualization", {"casual"}, "formal") == "casual"


# ── extract_choice_from_aliases ────────────────────────────────────────────

class TestExtractChoiceFromAliases:
    def test_direct_match(self):
        aliases = {"wedding": ("wedding", "engagement"), "casual": ("casual",)}
        assert extract_choice_from_aliases("for a wedding", aliases, "casual") == "wedding"

    def test_alias_match(self):
        aliases = {"wedding": ("wedding", "engagement"), "casual": ("casual", "everyday")}
        assert extract_choice_from_aliases("going to an engagement", aliases, "casual") == "wedding"

    def test_no_match_returns_default(self):
        aliases = {"wedding": ("wedding",), "casual": ("casual",)}
        assert extract_choice_from_aliases("for a party", aliases, "casual") == "casual"


# ── build_chat_request_profile ─────────────────────────────────────────────

class TestBuildChatRequestProfile:
    def test_greeting_returns_defaults(self):
        profile = build_chat_request_profile("hello")
        assert profile["occasion"] == "casual"
        assert profile["style"] == "minimal"
        assert profile["use_wardrobe"] is False
        assert profile["use_favorites"] is False

    def test_explicit_values(self):
        profile = build_chat_request_profile("what should I wear to a wedding in ethnic style under 5000")
        assert profile["occasion"] == "wedding"
        assert profile["style"] == "ethnic"
        assert profile["budget"] == 5000

    def test_wardrobe_keyword_detected(self):
        profile = build_chat_request_profile("suggest from my wardrobe")
        assert profile["use_wardrobe"] is True

    def test_favorite_keyword_detected(self):
        profile = build_chat_request_profile("check my saved favorites")
        assert profile["use_favorites"] is True

    def test_local_keyword_detected(self):
        profile = build_chat_request_profile("show local designers")
        assert profile["prioritize_local"] is True

    def test_trend_keyword_detected(self):
        profile = build_chat_request_profile("what is trendy right now")
        assert profile["prioritize_trend"] is True

    def test_under_budget_parsing(self):
        profile = build_chat_request_profile("give me something under 1500")
        assert profile["budget"] == 1500


# ── build_local_chat_response ──────────────────────────────────────────────

class TestBuildLocalChatResponse:
    def test_greeting_returns_help(self):
        response = build_local_chat_response("hello")
        assert "AI stylist" in response or "help" in response.lower()
        assert "wear" in response.lower() or "Try" in response

    def test_greeting_variants(self):
        for msg in ["hi", "hey", "good morning"]:
            response = build_local_chat_response(msg)
            assert "AI stylist" in response or "help" in response

    def test_fashion_query_returns_outfit(self, monkeypatch, sample_products):
        monkeypatch.setattr("backend.services.recommendations.load_products", lambda: sample_products)
        monkeypatch.setattr("backend.services.recommendations.load_trends", lambda: [])
        monkeypatch.setattr("backend.services.recommendations.load_wardrobe", lambda: [])
        monkeypatch.setattr("backend.services.recommendations.load_favorites", lambda: [])
        response = build_local_chat_response("what should I wear casually")
        assert "Shirt" in response or "Jeans" in response or "recommendation" in response

import json
import os
import re
from collections import Counter, deque
from typing import Any

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - handled at runtime
    OpenAI = None  # type: ignore[assignment]

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - handled at runtime
    load_dotenv = None  # type: ignore[assignment]

from ..config import DEFAULT_OPENAI_MODEL, DOTENV_PATH
from ..services.recommendations import load_products, load_trends, load_wardrobe, load_favorites

RECENT_CHAT_ITEMS: deque[list[str]] = deque(maxlen=6)

def build_chat_context() -> str:
    products = load_products()[:12]
    wardrobe = load_wardrobe()
    favorites_data = load_favorites()[:5]
    trends = load_trends()[:8]

    context = {
        "catalog_products": [
            {
                "name": product["name"],
                "category": product["category"],
                "price": product["price"],
                "brand": product["brand"],
                "occasions": product["occasions"],
                "styles": product["styles"],
                "designer_type": product["designer_type"],
                "buy_link": product.get("buy_link", ""),
            }
            for product in products
        ],
        "wardrobe_items": wardrobe,
        "favorites": favorites_data,
        "trend_signals": trends,
    }
    return json.dumps(context, ensure_ascii=False, indent=2)

if load_dotenv is not None:
    load_dotenv(DOTENV_PATH)

def get_openai_client() -> Any:
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None
    if OpenAI is None:
        raise RuntimeError("OpenAI SDK is not installed. Install it with `pip install openai`.")
    return OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")

def ask_openai_chatbot(message: str) -> str:
    client = get_openai_client()
    if client is None:
        raise RuntimeError("GROQ_API_KEY is not set.")

    prompt = (
        "You are a fashion stylist for the ModeMint app. "
        "Give practical outfit guidance using the provided wardrobe and store catalog. "
        "Prefer concise answers, mention specific items when relevant, keep prices in Rs., "
        "and offer one main recommendation with a short styling tip. "
        "CRITICAL: When referencing a catalog item, you MUST include a clickable link formatted "
        "in Markdown using the provided buy_link, e.g., `[Product Name](buy_link)`. Always use Markdown for links."
        "\n\nIf the user's message is a simple greeting (hi, hello, hey) or a non-fashion question, "
        "do NOT generate an outfit. Instead, greet them warmly and list what you can help with."
    )

    response = client.responses.create(
        model=DEFAULT_OPENAI_MODEL,
        instructions=prompt,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"User request:\n{message}\n\n"
                            f"Available app context:\n{build_chat_context()}"
                        ),
                    }
                ],
            }
        ],
    )
    return (getattr(response, "output_text", "") or "").strip()

def extract_budget_from_text(message: str) -> int:
    from backend.config import DEFAULT_BUDGET
    match = re.search(r"(\d{3,6})", message)
    if not match:
        return DEFAULT_BUDGET
    return max(500, int(match.group(1)))

def extract_choice(message: str, options: set[str], default: str) -> str:
    lowered = message.lower()
    words = set(lowered.split())
    for option in options:
        if option in lowered and (option in words or lowered == option):
            return option
    for option in options:
        if option in lowered:
            return option
    return default

def extract_choice_from_aliases(message: str, alias_map: dict[str, tuple[str, ...]], default: str) -> str:
    lowered = message.lower()
    for choice, aliases in alias_map.items():
        if choice in lowered:
            return choice
        for alias in aliases:
            if alias in lowered:
                return choice
    return default

def build_chat_request_profile(message: str) -> dict[str, Any]:
    from backend.config import DEFAULT_BUDGET, DEFAULT_OCCASION, DEFAULT_STYLE

    occasion_aliases = {
        "wedding": ("wedding", "engagement", "sangeet", "reception", "festive"),
        "casual": ("casual", "daily", "everyday", "brunch", "coffee", "weekend"),
        "party": ("party", "club", "night out", "concert", "birthday"),
        "college": ("college", "campus", "class", "uni", "university"),
        "formal": ("formal", "office", "meeting", "interview", "work", "corporate"),
    }
    style_aliases = {
        "minimal": ("minimal", "clean", "simple", "understated"),
        "streetwear": ("streetwear", "street", "edgy", "oversized", "urban"),
        "ethnic": ("ethnic", "traditional", "desi", "indian", "festive"),
        "classic": ("classic", "timeless", "elegant", "refined"),
        "chic": ("chic", "dressy", "glam", "feminine", "sleek"),
        "smart-casual": ("smart casual", "smart-casual", "polished", "semi formal", "semi-formal"),
    }

    lowered = message.lower()
    profile = {
        "occasion": extract_choice_from_aliases(message, occasion_aliases, DEFAULT_OCCASION),
        "style": extract_choice_from_aliases(message, style_aliases, DEFAULT_STYLE),
        "budget": extract_budget_from_text(message),
        "use_wardrobe": any(term in lowered for term in ("wardrobe", "closet", "own", "my clothes", "already have")),
        "use_favorites": any(term in lowered for term in ("favorite", "saved", "liked", "wishlist")),
        "prioritize_local": any(term in lowered for term in ("local", "indie", "small designer", "small brand")),
        "prioritize_trend": any(term in lowered for term in ("trend", "trendy", "viral", "fashion forward", "fashion-forward")),
    }

    if "under" in lowered and profile["budget"] == DEFAULT_BUDGET:
        budget_match = re.search(r"under\s*rs\.?\s*(\d{3,6})", lowered)
        if budget_match:
            profile["budget"] = max(500, int(budget_match.group(1)))

    return profile

def choose_outfit_for_message(outfits: list[dict[str, Any]], message: str) -> dict[str, Any]:
    if not outfits:
        return {}

    lowered = message.lower()
    ranked = outfits[: min(12, len(outfits))]

    if any(term in lowered for term in ("cheap", "budget", "affordable", "under")):
        ranked = sorted(ranked, key=lambda outfit: (outfit["total_price"], -outfit["score"]))
    elif any(term in lowered for term in ("trend", "trendy", "statement", "bold")):
        ranked = sorted(ranked, key=lambda outfit: (outfit["trend_score"], outfit["score"]), reverse=True)
    elif any(term in lowered for term in ("local", "indie", "small designer", "small brand")):
        ranked = sorted(
            ranked,
            key=lambda outfit: sum(1 for item in outfit["items"].values() if item["designer_type"] == "local"),
            reverse=True,
        )

    recent_counts = Counter(item_id for outfit_items in RECENT_CHAT_ITEMS for item_id in outfit_items)

    def diversity_key(outfit: dict[str, Any]) -> tuple[float, float, int]:
        item_ids = [str(item.get("id", "")) for item in outfit["items"].values()]
        repeated_items = sum(recent_counts[item_id] for item_id in item_ids)
        budget_gap = abs(outfit["total_price"] - (extract_budget_from_text(message) or outfit["total_price"]))
        return (repeated_items, budget_gap, -int(outfit["total_price"]))

    diversified = sorted(ranked, key=diversity_key)
    best_penalty = diversity_key(diversified[0])[0]
    best_candidates = [outfit for outfit in diversified if diversity_key(outfit)[0] == best_penalty]

    seed = sum(ord(char) for char in lowered) % len(best_candidates)
    selected = best_candidates[seed]
    RECENT_CHAT_ITEMS.append([str(item.get("id", "")) for item in selected["items"].values()])
    return selected

def build_outfit_lines(outfit: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for category, item in outfit["items"].items():
        lines.append(f"{category.title()}: {item['name']} by {item['brand']} for Rs. {item['price']:,}.")
    return lines

def detect_fashion_intent(message: str) -> bool:
    lowered = message.lower().strip()
    fashion_terms = {
        "wear", "outfit", "style", "fashion", "dress", "look", "clothes", "shirt", "top",
        "bottom", "jeans", "shoes", "sneakers", "accessory", "watch", "bag", "jacket",
        "coat", "sweater", "hoodie", "kurta", "blazer", "suit", "trousers", "chinos",
        "shorts", "skirt", "formal", "casual", "party", "wedding", "college", "office",
        "trend", "budget", "price", "color", "wardrobe", "closet", "favorite", "stylist",
        "recommend", "suggest", "matching", "combine", "what should i",
    }
    return any(term in lowered for term in fashion_terms)

def build_local_chat_response(message: str) -> str:
    from .recommendations import recommend_outfits_with_limit, generate_wardrobe_outfits
    from ..config import DEFAULT_BUDGET

    if not detect_fashion_intent(message):
        return (
            "Hi! I'm ModeMint's AI stylist. I can help you with:\n\n"
            "\u2022 Outfit recommendations by occasion, style, and budget\n"
            "\u2022 Wardrobe management and styling from your own clothes\n"
            "\u2022 Product and trend insights from the store\n"
            "\u2022 Saving and recalling your favorite looks\n\n"
            "Try something like:\n"
            '\u2022 "What should I wear to a college fest under 3000?"\n'
            '\u2022 "Give me a streetwear look for a party"\n'
            '\u2022 "Suggest a formal outfit from my wardrobe"'
        )

    profile = build_chat_request_profile(message)
    occasion = profile["occasion"]
    style = profile["style"]
    budget = profile["budget"]
    wardrobe_outfits = generate_wardrobe_outfits(occasion, style)

    if profile["use_wardrobe"] and wardrobe_outfits:
        top_outfit = wardrobe_outfits[0]
        item_names = ", ".join(item["name"] for item in top_outfit["items"].values())
        return (
            f"Built from your wardrobe for {occasion} in a {style} direction: {item_names}. "
            f"Styling tip: {top_outfit['reasons'][0] if top_outfit['reasons'] else 'Keep the colors coordinated.'}"
        )

    outfits = recommend_outfits_with_limit(occasion, style, budget, limit=30)

    if outfits:
        top_outfit = choose_outfit_for_message(outfits, message)
        opener = f"Here is a {style} look for {occasion} under Rs. {budget:,}."
        if budget == DEFAULT_BUDGET and not re.search(r"\d{3,6}", message):
            opener = f"Based on your prompt, I would start with this {style} look for {occasion}."

        lines = [
            opener,
            f"Total: Rs. {top_outfit['total_price']:,}.",
            "",
        ]

        lines.extend(build_outfit_lines(top_outfit))

        styling_tip = top_outfit['reasons'][0] if top_outfit['reasons'] else 'Keep the look simple and balanced.'
        if profile["prioritize_local"]:
            styling_tip = "This pick leans into local labels while keeping the outfit balanced."
        elif profile["prioritize_trend"]:
            styling_tip = "This direction leans into the strongest trend score in the current catalog."

        lines.extend(
            [
                "",
                f"Main recommendation: {', '.join(item['name'] for item in top_outfit['items'].values())}.",
                f"Styling tip: {styling_tip}",
            ]
        )
        return "\n".join(lines)

    if wardrobe_outfits:
        top_outfit = wardrobe_outfits[0]
        item_names = ", ".join(item["name"] for item in top_outfit["items"].values())
        return (
            f"I could not find a store outfit under Rs. {budget:,}, but your wardrobe can still work. "
            f"Try {item_names}. Styling tip: {top_outfit['reasons'][0] if top_outfit['reasons'] else 'Keep the colors coordinated.'}"
        )

    if profile["use_favorites"]:
        favorites = load_favorites()
        if favorites:
            favorite = favorites[0]
            names = ", ".join(item["name"] for item in favorite.get("outfit", {}).get("items", {}).values())
            return f"Your saved looks can still guide this. Start from {favorite.get('name', 'your saved outfit')}: {names}."

    return (
        f"I could not find a strong match for {occasion} in {style} style right now. "
        "Try raising the budget a little or add more wardrobe items."
    )

import json
import os
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
    import re
    from backend.config import DEFAULT_BUDGET
    match = re.search(r"(\d{3,6})", message)
    if not match:
        return DEFAULT_BUDGET
    return max(500, int(match.group(1)))

def extract_choice(message: str, options: set[str], default: str) -> str:
    lowered = message.lower()
    for option in options:
        if option in lowered:
            return option
    return default

def build_local_chat_response(message: str) -> str:
    from .recommendations import recommend_outfits, generate_wardrobe_outfits
    from ..config import DEFAULT_BUDGET, DEFAULT_OCCASION, DEFAULT_STYLE
    occasion = extract_choice(message, {"wedding", "casual", "party", "college", "formal"}, DEFAULT_OCCASION)
    style = extract_choice(
        message,
        {"minimal", "streetwear", "ethnic", "classic", "chic", "smart-casual"},
        DEFAULT_STYLE,
    )
    budget = extract_budget_from_text(message)
    outfits = recommend_outfits(occasion, style, budget)

    if outfits:
        top_outfit = outfits[0]
        lines = [
            f"Here is a {style} look for {occasion} under Rs. {budget:,}.",
            f"Total: Rs. {top_outfit['total_price']:,}.",
            "",
        ]
        for category, item in top_outfit["items"].items():
            lines.append(f"{category.title()}: {item['name']} by {item['brand']} for Rs. {item['price']:,}.")
        lines.extend(
            [
                "",
                f"Main recommendation: {', '.join(item['name'] for item in top_outfit['items'].values())}.",
                f"Styling tip: {top_outfit['reasons'][0] if top_outfit['reasons'] else 'Keep the look simple and balanced.'}",
            ]
        )
        return "\n".join(lines)

    wardrobe_outfits = generate_wardrobe_outfits(occasion, style)
    if wardrobe_outfits:
        top_outfit = wardrobe_outfits[0]
        item_names = ", ".join(item["name"] for item in top_outfit["items"].values())
        return (
            f"I could not find a store outfit under Rs. {budget:,}, but your wardrobe can still work. "
            f"Try {item_names}. Styling tip: {top_outfit['reasons'][0] if top_outfit['reasons'] else 'Keep the colors coordinated.'}"
        )

    return (
        f"I could not find a strong match for {occasion} in {style} style right now. "
        "Try raising the budget a little or add more wardrobe items."
    )
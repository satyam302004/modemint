import itertools
from typing import Any, Dict, List

from ..config import (
    DEFAULT_BUDGET,
    DEFAULT_OCCASION,
    DEFAULT_STYLE,
    FAVORITES_FILE,
    PRODUCTS_FILE,
    REQUIRED_CATEGORIES,
    TRENDS_FILE,
    WARDROBE_FILE,
    WARDROBE_REQUIRED_CATEGORIES,
)
from ..utils.data_loader import load_json, save_json

def normalize_product(product: dict[str, Any]) -> dict[str, Any]:
    occasions = [str(value).strip().lower() for value in product.get("occasions", [])]
    styles = [str(value).strip().lower() for value in product.get("styles", [])]
    return {
        "id": str(product.get("id", "")).strip(),
        "name": str(product.get("name", "")).strip(),
        "category": str(product.get("category", "")).strip().lower(),
        "price": int(product.get("price", 0)),
        "brand": str(product.get("brand", "")).strip(),
        "designer_type": str(product.get("designer_type", "local")).strip().lower(),
        "occasions": occasions,
        "styles": styles,
        "trend_score": float(product.get("trend_score", 0)),
        "buy_link": str(product.get("buy_link", "")).strip(),
        "image": str(product.get("image", "")).strip(),
        "description": str(product.get("description", "")).strip(),
    }

def normalize_wardrobe_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id", "")).strip(),
        "name": str(item.get("name", "")).strip(),
        "category": str(item.get("category", "")).strip().lower(),
        "color": str(item.get("color", "unknown")).strip().lower(),
        "style": str(item.get("style", "casual")).strip().lower(),
        "occasion": str(item.get("occasion", DEFAULT_OCCASION)).strip().lower(),
        "image": str(item.get("image", "")).strip(),
    }

def normalize_trend(trend: dict[str, Any]) -> dict[str, Any]:
    def normalize_list(values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return [str(value).strip().lower() for value in values if str(value).strip()]

    return {
        "id": str(trend.get("id", "")).strip(),
        "keyword": str(trend.get("keyword", "")).strip(),
        "source": str(trend.get("source", "manual")).strip(),
        "region": str(trend.get("region", "global")).strip().lower(),
        "season": str(trend.get("season", "all")).strip().lower(),
        "year": int(trend.get("year", 0) or 0),
        "score": float(trend.get("score", 0)),
        "styles": normalize_list(trend.get("styles", [])),
        "occasions": normalize_list(trend.get("occasions", [])),
        "colors": normalize_list(trend.get("colors", [])),
        "categories": normalize_list(trend.get("categories", [])),
        "notes": str(trend.get("notes", "")).strip(),
    }

def load_products() -> list[dict[str, Any]]:
    products = load_json(PRODUCTS_FILE, [])
    return [normalize_product(product) for product in products]

def load_trends() -> list[dict[str, Any]]:
    trends = load_json(TRENDS_FILE, [])
    return [normalize_trend(trend) for trend in trends]

def load_favorites() -> list[dict[str, Any]]:
    return load_json(FAVORITES_FILE, [])

def load_wardrobe() -> list[dict[str, Any]]:
    items = load_json(WARDROBE_FILE, [])
    return [normalize_wardrobe_item(item) for item in items]

def filter_products(
    products: list[dict[str, Any]],
    occasion: str,
    style: str,
    budget: int,
) -> dict[str, list[dict[str, Any]]]:
    shortlisted: dict[str, list[dict[str, Any]]] = {category: [] for category in REQUIRED_CATEGORIES}

    for product in products:
        if product["price"] > budget:
            continue
        if occasion not in product["occasions"]:
            continue
        if style not in product["styles"] and "versatile" not in product["styles"]:
            continue
        if product["category"] in shortlisted:
            shortlisted[product["category"]].append(product)

    return shortlisted

def trend_matches_product(product: dict[str, Any], trend: dict[str, Any], occasion: str, style: str) -> bool:
    if trend["styles"] and style not in trend["styles"] and not set(product["styles"]).intersection(trend["styles"]):
        return False
    if trend["occasions"] and occasion not in trend["occasions"] and not set(product["occasions"]).intersection(trend["occasions"]):
        return False
    if trend["categories"] and product["category"] not in trend["categories"]:
        return False
    return True

def compute_trend_boost(items: dict[str, dict[str, Any]], occasion: str, style: str) -> dict[str, Any]:
    trends = load_trends()
    matched_keywords: list[str] = []
    matched_scores: list[float] = []

    for trend in trends:
        if any(trend_matches_product(product, trend, occasion, style) for product in items.values()):
            matched_keywords.append(trend["keyword"])
            matched_scores.append(trend["score"])

    if not matched_scores:
        return {"trend_boost": 0.0, "trend_keywords": []}

    trend_boost = round(sum(matched_scores[:3]) / len(matched_scores[:3]) / 4, 2)
    return {
        "trend_boost": trend_boost,
        "trend_keywords": matched_keywords[:3],
    }

def build_reasons(outfit: dict[str, Any], occasion: str, style: str, budget: int) -> list[str]:
    reasons = [
        f"Built for {occasion} dressing",
        f"Matches a {style} style direction",
    ]

    total_price = outfit["total_price"]
    if total_price <= budget * 0.7:
        reasons.append("Comfortably under budget")
    elif total_price <= budget:
        reasons.append("Fits within your budget")

    local_count = sum(1 for item in outfit["items"].values() if item["designer_type"] == "local")
    if local_count >= 2:
        reasons.append("Highlights local designers")

    if outfit["trend_score"] >= 7:
        reasons.append("Leans into current trends")
    if outfit.get("trend_keywords"):
        reasons.append(f"Trend match: {outfit['trend_keywords'][0]}")

    return reasons[:4]

def score_outfit(
    items: dict[str, dict[str, Any]],
    occasion: str,
    style: str,
    budget: int,
) -> dict[str, Any]:
    total_price = sum(item["price"] for item in items.values())
    trend_score = round(sum(item["trend_score"] for item in items.values()) / len(items), 2)
    local_bonus = sum(1 for item in items.values() if item["designer_type"] == "local") * 1.25
    style_matches = sum(1 for item in items.values() if style in item["styles"] or "versatile" in item["styles"])
    occasion_matches = sum(1 for item in items.values() if occasion in item["occasions"])
    budget_bonus = max(0, (budget - total_price) / max(budget, 1)) * 4
    trend_data = compute_trend_boost(items, occasion, style)

    score = (
        occasion_matches * 2.0
        + style_matches * 1.5
        + trend_score
        + trend_data["trend_boost"]
        + local_bonus
        + budget_bonus
    )

    outfit = {
        "items": items,
        "total_price": total_price,
        "trend_score": trend_score,
        "trend_boost": trend_data["trend_boost"],
        "trend_keywords": trend_data["trend_keywords"],
        "score": round(score, 2),
        "designer_focus": local_bonus > 0,
    }
    outfit["reasons"] = build_reasons(outfit, occasion, style, budget)
    return outfit

def recommend_outfits(occasion: str, style: str, budget: int) -> list[dict[str, Any]]:
    products = load_products()
    shortlisted = filter_products(products, occasion, style, budget)

    if any(not shortlisted[category] for category in REQUIRED_CATEGORIES):
        return []

    combinations = itertools.product(*(shortlisted[category] for category in REQUIRED_CATEGORIES))
    outfits: list[dict[str, Any]] = []

    for combo in combinations:
        items = {category: product for category, product in zip(REQUIRED_CATEGORIES, combo)}
        total_price = sum(item["price"] for item in items.values())
        if total_price > budget:
            continue
        outfits.append(score_outfit(items, occasion, style, budget))

    outfits.sort(key=lambda outfit: (outfit["score"], outfit["trend_score"]), reverse=True)
    return outfits[:6]

def score_wardrobe_outfit(
    items: dict[str, dict[str, Any]],
    occasion: str,
    style: str,
) -> dict[str, Any]:
    score = 5.0
    reasons: list[str] = []

    matching_style = sum(1 for item in items.values() if item["style"] == style)
    matching_occasion = sum(1 for item in items.values() if item["occasion"] in {occasion, "any", "versatile"})
    colors = [item["color"] for item in items.values()]
    unique_colors = len(set(color for color in colors if color != "unknown"))

    score += matching_style * 1.5
    score += matching_occasion * 1.25

    if matching_style >= 2:
        reasons.append(f"Strong {style} match")
    if matching_occasion >= 2:
        reasons.append(f"Works well for {occasion}")
    if unique_colors <= 2:
        score += 1.5
        reasons.append("Colors coordinate cleanly")
    if any(item["category"] == "accessory" for item in items.values()):
        score += 0.5
        reasons.append("Finished with an accessory")

    return {
        "items": items,
        "score": round(score, 2),
        "reasons": reasons[:4] or ["Balanced everyday combination"],
    }

def generate_wardrobe_outfits(occasion: str, style: str) -> list[dict[str, Any]]:
    wardrobe = load_wardrobe()
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in WARDROBE_REQUIRED_CATEGORIES}
    accessories: list[dict[str, Any]] = []

    for item in wardrobe:
        category = item["category"]
        if category in grouped:
            grouped[category].append(item)
        elif category == "accessory":
            accessories.append(item)

    if any(not grouped[category] for category in WARDROBE_REQUIRED_CATEGORIES):
        return []

    outfits: list[dict[str, Any]] = []
    combinations = itertools.product(*(grouped[category] for category in WARDROBE_REQUIRED_CATEGORIES))

    for combo in combinations:
        base_items = {category: product for category, product in zip(WARDROBE_REQUIRED_CATEGORIES, combo)}
        outfit = score_wardrobe_outfit(base_items, occasion, style)
        outfits.append(outfit)

        for accessory in accessories:
            styled_items = dict(base_items)
            styled_items["accessory"] = accessory
            outfits.append(score_wardrobe_outfit(styled_items, occasion, style))

    outfits.sort(key=lambda outfit: outfit["score"], reverse=True)
    return outfits[:8]
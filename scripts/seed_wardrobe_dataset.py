from __future__ import annotations

import json
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


BASE_URL = "http://localhost:5000"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "scripts" / "wardrobe_seed_images"
REPORT_PATH = PROJECT_ROOT / "docs" / "wardrobe_seed_report.json"
WARDROBE_FILE = PROJECT_ROOT / "backend" / "data" / "wardrobe.json"

LOCAL_SAMPLES = {
    "top": PROJECT_ROOT / "frontend" / "sample-shirt.jpg",
    "bottom": PROJECT_ROOT / "frontend" / "sample-jeans.jpg",
    "shoes": PROJECT_ROOT / "frontend" / "sample-shoes.jpg",
}


@dataclass
class SeedItem:
    name: str
    category: str
    color: str
    style: str
    occasion: str
    source_kind: str
    source_value: str
    filename: str


def build_seed_items() -> list[SeedItem]:
    baseline_items = [
        SeedItem("White Campus Tee", "top", "white", "casual", "college", "local", "top", "white-campus-tee.jpg"),
        SeedItem("White Minimal Tee", "top", "white", "minimal", "casual", "local", "top", "white-minimal-tee.jpg"),
        SeedItem("White Weekend Tee", "top", "white", "casual", "casual", "local", "top", "white-weekend-tee.jpg"),
        SeedItem("White Layering Tee", "top", "white", "streetwear", "college", "local", "top", "white-layering-tee.jpg"),
        SeedItem("White Basics Tee", "top", "white", "smart-casual", "casual", "local", "top", "white-basics-tee.jpg"),
        SeedItem("Blue Street Jeans", "bottom", "blue", "streetwear", "college", "local", "bottom", "blue-street-jeans.jpg"),
        SeedItem("Blue Everyday Jeans", "bottom", "blue", "casual", "casual", "local", "bottom", "blue-everyday-jeans.jpg"),
        SeedItem("Blue Weekend Denim", "bottom", "blue", "casual", "college", "local", "bottom", "blue-weekend-denim.jpg"),
        SeedItem("Blue Relaxed Jeans", "bottom", "blue", "streetwear", "casual", "local", "bottom", "blue-relaxed-jeans.jpg"),
        SeedItem("Blue Classic Jeans", "bottom", "blue", "classic", "college", "local", "bottom", "blue-classic-jeans.jpg"),
        SeedItem("Red Flex Sneaker", "shoes", "red", "streetwear", "college", "local", "shoes", "red-flex-sneaker.jpg"),
        SeedItem("Red Training Sneaker", "shoes", "red", "casual", "college", "local", "shoes", "red-training-sneaker.jpg"),
        SeedItem("Red Sport Sneaker", "shoes", "red", "streetwear", "casual", "local", "shoes", "red-sport-sneaker.jpg"),
        SeedItem("Red Daily Sneaker", "shoes", "red", "casual", "college", "local", "shoes", "red-daily-sneaker.jpg"),
        SeedItem("Red Statement Sneaker", "shoes", "red", "streetwear", "party", "local", "shoes", "red-statement-sneaker.jpg"),
    ]

    download_specs = [
        SeedItem("Black Oxford Shirt", "top", "black", "classic", "formal", "download", "fashion,shirt", "black-oxford-shirt.jpg"),
        SeedItem("Beige Linen Shirt", "top", "beige", "minimal", "casual", "download", "fashion,linen-shirt", "beige-linen-shirt.jpg"),
        SeedItem("Blue Denim Jacket", "top", "blue", "streetwear", "college", "download", "fashion,jacket", "blue-denim-jacket.jpg"),
        SeedItem("Olive Bomber Jacket", "top", "olive", "streetwear", "party", "download", "fashion,bomber-jacket", "olive-bomber-jacket.jpg"),
        SeedItem("White Festive Kurta", "top", "white", "ethnic", "wedding", "download", "fashion,kurta", "white-festive-kurta.jpg"),
        SeedItem("Grey City Hoodie", "top", "grey", "streetwear", "college", "download", "fashion,hoodie", "grey-city-hoodie.jpg"),
        SeedItem("Navy Sharp Blazer", "top", "navy", "smart-casual", "formal", "download", "fashion,blazer", "navy-sharp-blazer.jpg"),
        SeedItem("Cream Cozy Sweater", "top", "cream", "chic", "casual", "download", "fashion,sweater", "cream-cozy-sweater.jpg"),
        SeedItem("Emerald Party Top", "top", "green", "chic", "party", "download", "fashion,party-top", "emerald-party-top.jpg"),
        SeedItem("Black Winter Coat", "top", "black", "formal", "formal", "download", "fashion,coat", "black-winter-coat.jpg"),
        SeedItem("Tailored Black Trousers", "bottom", "black", "formal", "formal", "download", "fashion,trousers", "tailored-black-trousers.jpg"),
        SeedItem("Beige Casual Chinos", "bottom", "beige", "smart-casual", "casual", "download", "fashion,chinos", "beige-casual-chinos.jpg"),
        SeedItem("Olive Cargo Pants", "bottom", "olive", "streetwear", "college", "download", "fashion,cargo-pants", "olive-cargo-pants.jpg"),
        SeedItem("Grey Office Pants", "bottom", "grey", "classic", "formal", "download", "fashion,pants", "grey-office-pants.jpg"),
        SeedItem("Wide Leg Denim", "bottom", "blue", "casual", "college", "download", "fashion,wide-leg-jeans", "wide-leg-denim.jpg"),
        SeedItem("Pleated Chic Trousers", "bottom", "black", "chic", "party", "download", "fashion,pleated-trousers", "pleated-chic-trousers.jpg"),
        SeedItem("Festive Palazzo", "bottom", "maroon", "ethnic", "wedding", "download", "fashion,palazzo", "festive-palazzo.jpg"),
        SeedItem("Black Summer Shorts", "bottom", "black", "casual", "casual", "download", "fashion,shorts", "black-summer-shorts.jpg"),
        SeedItem("White Flow Skirt", "bottom", "white", "chic", "party", "download", "fashion,skirt", "white-flow-skirt.jpg"),
        SeedItem("Blue Classic Jeans Plus", "bottom", "blue", "classic", "casual", "download", "fashion,jeans", "blue-classic-jeans-plus.jpg"),
        SeedItem("White Court Sneakers", "shoes", "white", "streetwear", "college", "download", "fashion,sneakers", "white-court-sneakers.jpg"),
        SeedItem("Black Formal Loafers", "shoes", "black", "formal", "formal", "download", "fashion,loafers", "black-formal-loafers.jpg"),
        SeedItem("Tan Party Heels", "shoes", "tan", "chic", "party", "download", "fashion,heels", "tan-party-heels.jpg"),
        SeedItem("Brown Leather Boots", "shoes", "brown", "classic", "casual", "download", "fashion,boots", "brown-leather-boots.jpg"),
        SeedItem("Ethnic Wedding Juttis", "shoes", "gold", "ethnic", "wedding", "download", "fashion,jutti", "ethnic-wedding-juttis.jpg"),
        SeedItem("Silver Formal Watch", "accessory", "silver", "classic", "formal", "download", "fashion,watch", "silver-formal-watch.jpg"),
        SeedItem("Black Leather Belt", "accessory", "black", "classic", "formal", "download", "fashion,belt", "black-leather-belt.jpg"),
        SeedItem("Gold Party Earrings", "accessory", "gold", "chic", "party", "download", "fashion,earrings", "gold-party-earrings.jpg"),
        SeedItem("Urban Sunglasses", "accessory", "black", "casual", "college", "download", "fashion,sunglasses", "urban-sunglasses.jpg"),
        SeedItem("Minimal Tote Bag", "accessory", "beige", "minimal", "casual", "download", "fashion,tote-bag", "minimal-tote-bag.jpg"),
        SeedItem("Printed Wedding Scarf", "accessory", "red", "ethnic", "wedding", "download", "fashion,scarf", "printed-wedding-scarf.jpg"),
        SeedItem("Statement Necklace", "accessory", "gold", "chic", "party", "download", "fashion,necklace", "statement-necklace.jpg"),
        SeedItem("Streetwear Cap", "accessory", "black", "streetwear", "college", "download", "fashion,cap", "streetwear-cap.jpg"),
        SeedItem("Evening Clutch", "accessory", "black", "chic", "wedding", "download", "fashion,clutch", "evening-clutch.jpg"),
        SeedItem("Formal Silk Tie", "accessory", "navy", "formal", "formal", "download", "fashion,tie", "formal-silk-tie.jpg"),
    ]

    return baseline_items + download_specs


def ensure_dirs() -> None:
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)


def backup_wardrobe_file() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = WARDROBE_FILE.with_name(f"wardrobe.backup_{timestamp}.json")
    shutil.copy2(WARDROBE_FILE, backup)
    return backup


def build_download_url(query: str, lock_id: int) -> str:
    return f"https://loremflickr.com/800/800/{query}?lock={lock_id}"


def prepare_source_images(seed_items: list[SeedItem]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    download_counter = 1
    session = requests.Session()

    for item in seed_items:
        target = DATASET_DIR / item.filename
        if target.exists():
            prepared.append({"item": item, "source_path": str(target), "download_url": None})
            continue

        if item.source_kind == "local":
            source_path = LOCAL_SAMPLES[item.source_value]
            shutil.copy2(source_path, target)
            prepared.append({"item": item, "source_path": str(target), "download_url": None})
            continue

        url = build_download_url(item.source_value, download_counter)
        download_counter += 1
        response = session.get(url, timeout=45)
        response.raise_for_status()
        target.write_bytes(response.content)
        prepared.append({"item": item, "source_path": str(target), "download_url": url})
        time.sleep(0.2)

    return prepared


def clear_existing_wardrobe(session: requests.Session) -> list[str]:
    response = session.get(f"{BASE_URL}/wardrobe", timeout=30)
    response.raise_for_status()
    items = response.json()
    deleted: list[str] = []
    for item in items:
        item_id = item.get("id")
        if not item_id:
            continue
        delete_response = session.delete(f"{BASE_URL}/wardrobe/{item_id}", timeout=30)
        delete_response.raise_for_status()
        deleted.append(item_id)
    return deleted


def upload_and_add_items(prepared_items: list[dict[str, Any]]) -> dict[str, Any]:
    session = requests.Session()
    deleted_ids = clear_existing_wardrobe(session)
    added: list[dict[str, Any]] = []
    detection_summary: list[dict[str, Any]] = []

    for entry in prepared_items:
        item: SeedItem = entry["item"]
        source_path = Path(entry["source_path"])
        with source_path.open("rb") as handle:
            upload_response = session.post(
                f"{BASE_URL}/wardrobe/upload",
                files={"image": (source_path.name, handle, "image/jpeg")},
                timeout=60,
            )
        upload_response.raise_for_status()
        upload_data = upload_response.json()
        analysis = upload_data.get("analysis", {})

        payload = {
            "name": item.name,
            "category": item.category,
            "color": item.color,
            "style": item.style,
            "occasion": item.occasion,
            "image": upload_data.get("image", ""),
        }
        add_response = session.post(f"{BASE_URL}/wardrobe", json=payload, timeout=30)
        add_response.raise_for_status()
        added_item = add_response.json()
        added.append(added_item)
        detection_summary.append(
            {
                "name": item.name,
                "category": item.category,
                "source_kind": item.source_kind,
                "download_url": entry["download_url"],
                "source_path": str(source_path),
                "saved_image": upload_data.get("image", ""),
                "analysis": analysis,
            }
        )

    scenarios = []
    for occasion, style in [
        ("college", "streetwear"),
        ("casual", "minimal"),
        ("formal", "classic"),
        ("party", "chic"),
        ("wedding", "ethnic"),
    ]:
        response = session.post(
            f"{BASE_URL}/wardrobe/generate",
            json={"occasion": occasion, "style": style},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        scenarios.append(
            {
                "occasion": occasion,
                "style": style,
                "count": len(data.get("outfits", [])),
                "top_score": data.get("outfits", [{}])[0].get("score") if data.get("outfits") else None,
            }
        )

    return {
        "deleted_ids": deleted_ids,
        "added_count": len(added),
        "added_items": added,
        "detection_summary": detection_summary,
        "generation_checks": scenarios,
    }


def main() -> None:
    ensure_dirs()
    backup_path = backup_wardrobe_file()
    seed_items = build_seed_items()
    prepared = prepare_source_images(seed_items)
    result = upload_and_add_items(prepared)
    report = {
        "generated_at": datetime.now().isoformat(),
        "project_root": str(PROJECT_ROOT),
        "backup_file": str(backup_path),
        "dataset_dir": str(DATASET_DIR),
        "target_count": len(seed_items),
        "result": result,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "backup_file": str(backup_path),
        "dataset_dir": str(DATASET_DIR),
        "added_count": result["added_count"],
        "generation_checks": result["generation_checks"],
        "report": str(REPORT_PATH),
    }, indent=2))


if __name__ == "__main__":
    main()

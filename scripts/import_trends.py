from __future__ import annotations

import json
import os
import sys
from typing import Any


BASE_DIR = os.path.dirname(__file__)
OUTPUT_PATH = os.path.join(BASE_DIR, "trends.json")


def normalize_list(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [part.strip() for part in values.split(",")]
    if not isinstance(values, list):
        return []
    return [str(value).strip().lower() for value in values if str(value).strip()]


def normalize_entry(entry: dict[str, Any], index: int) -> dict[str, Any]:
    keyword = str(entry.get("keyword", "")).strip()
    if not keyword:
        raise ValueError(f"Entry {index + 1} is missing 'keyword'.")

    return {
        "id": str(entry.get("id", f"trend-{index + 1:03d}")).strip(),
        "keyword": keyword,
        "source": str(entry.get("source", "pinterest-import")).strip(),
        "region": str(entry.get("region", "global")).strip().lower(),
        "season": str(entry.get("season", "all")).strip().lower(),
        "year": int(entry.get("year", 0) or 0),
        "score": float(entry.get("score", 0) or 0),
        "styles": normalize_list(entry.get("styles")),
        "occasions": normalize_list(entry.get("occasions")),
        "colors": normalize_list(entry.get("colors")),
        "categories": normalize_list(entry.get("categories")),
        "notes": str(entry.get("notes", "")).strip(),
    }


def load_source(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as file:
        raw = json.load(file)
    if not isinstance(raw, list):
        raise ValueError("Source file must contain a JSON array of trend entries.")
    return [normalize_entry(entry, index) for index, entry in enumerate(raw)]


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python import_pinterest_trends.py <source-json-path>")
        return 1

    source_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(source_path):
        print(f"Source file not found: {source_path}")
        return 1

    trends = load_source(source_path)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(trends, file, indent=2, ensure_ascii=False)

    print(f"Imported {len(trends)} trends into {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

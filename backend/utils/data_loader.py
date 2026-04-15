import json
import os
from typing import Any

def load_json(path: str, fallback: Any = None) -> Any:
    if not os.path.exists(path):
        return fallback or []
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)

def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
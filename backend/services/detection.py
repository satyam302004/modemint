from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any


@dataclass(frozen=True)
class DetectionItem:
    type: str
    name: str
    color: str = "unknown"
    style: str = "casual"


_MODEL = None
_MODEL_NAMES: dict[int, str] | None = None

ALLOWED_LABELS = {
    # Fashion-ish
    "t-shirt",
    "shirt",
    "jacket",
    "coat",
    "pants",
    "jeans",
    "shoe",
    "sneaker",
    # COCO label that often appears and is useful
    "tie",
}

LABEL_TO_ITEM = {
    "t-shirt": {"category": "top", "name": "T-Shirt", "style": "casual", "occasion": "casual"},
    "shirt": {"category": "top", "name": "Shirt", "style": "classic", "occasion": "formal"},
    "jacket": {"category": "top", "name": "Jacket", "style": "streetwear", "occasion": "party"},
    "coat": {"category": "top", "name": "Coat", "style": "formal", "occasion": "formal"},
    "pants": {"category": "bottom", "name": "Pants", "style": "casual", "occasion": "college"},
    "jeans": {"category": "bottom", "name": "Jeans", "style": "streetwear", "occasion": "college"},
    "shoe": {"category": "shoes", "name": "Shoes", "style": "casual", "occasion": "casual"},
    "sneaker": {"category": "shoes", "name": "Sneakers", "style": "streetwear", "occasion": "college"},
    "tie": {"category": "accessory", "name": "Tie", "style": "formal", "occasion": "formal"},
}


def _get_model():
    global _MODEL, _MODEL_NAMES
    if _MODEL is not None:
        return _MODEL

    # Import lazily so the rest of the backend can run even if
    # ultralytics isn't installed yet.
    from ultralytics import YOLO  # type: ignore

    _MODEL = YOLO("static/yolov8n.pt")
    _MODEL_NAMES = getattr(_MODEL, "names", None)
    return _MODEL


def _guess_from_filename(image_path: str, color: str) -> dict[str, Any]:
    stem = os.path.splitext(os.path.basename(image_path))[0].lower()
    for label, item in LABEL_TO_ITEM.items():
        token = label.replace("-", "")
        if label in stem or token in stem:
            return {
                "items": [
                    {
                        "category": item["category"],
                        "name": f"{color.title()} {item['name']}".strip() if color != "unknown" else item["name"],
                        "color": color,
                        "style": item["style"],
                        "occasion": item["occasion"],
                    }
                ],
                "labels": [label],
                "source": "filename",
            }

    return {
        "items": [
            {
                "category": "top",
                "name": f"{color.title()} Clothing".strip() if color != "unknown" else "Clothing Item",
                "color": color,
                "style": "casual",
                "occasion": "casual",
            }
        ],
        "labels": [],
        "source": "fallback",
    }


def _label_for_class(cls_id: int) -> str:
    if _MODEL_NAMES and cls_id in _MODEL_NAMES:
        return str(_MODEL_NAMES[cls_id])
    return str(cls_id)


def get_dominant_color(image_path: str) -> str:
    """
    Very lightweight dominant-color heuristic.
    Returns: 'white', 'black', or 'unknown'.
    """
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception:
        return "unknown"

    image = cv2.imread(image_path)
    if image is None:
        return "unknown"

    image = cv2.resize(image, (100, 100))
    pixels = image.reshape((-1, 3)).astype(np.float32)
    avg_bgr = np.mean(pixels, axis=0)  # B, G, R

    if avg_bgr[0] > 150 and avg_bgr[1] > 150 and avg_bgr[2] > 150:
        return "white"
    if avg_bgr[0] < 50 and avg_bgr[1] < 50 and avg_bgr[2] < 50:
        return "black"
    return "unknown"


def detect_clothing(image_path: str) -> dict[str, Any]:
    """
    Runs a pre-trained YOLO model and returns:
      - items: a list of wardrobe items (best-effort mapping)
      - labels: raw labels detected by the model

    Note: yolov8n.pt is trained on COCO (general objects), not fashion-specific.
    The mapping below is intentionally conservative and may return empty items.
    """
    color = get_dominant_color(image_path)
    try:
        model = _get_model()
        results = model(image_path)
    except Exception:
        return _guess_from_filename(image_path, color)

    labels: list[str] = []
    items: list[dict[str, str]] = []

    for r in results:
        boxes = getattr(r, "boxes", None)
        if boxes is None:
            continue

        for box in boxes:
            cls_val = getattr(box, "cls", None)
            if cls_val is None or len(cls_val) == 0:
                continue

            cls_id = int(cls_val[0])
            label = _label_for_class(cls_id).lower()
            labels.append(label)

            # Filter noise early (only keep labels we can map).
            if label not in ALLOWED_LABELS:
                continue

            mapped = LABEL_TO_ITEM.get(label)
            if mapped is None:
                continue

            items.append(
                {
                    "category": mapped["category"],
                    "name": f"{color.title()} {mapped['name']}".strip() if color != "unknown" else mapped["name"],
                    "color": color,
                    "style": mapped["style"],
                    "occasion": mapped["occasion"],
                }
            )

    # De-duplicate items by (category, name).
    seen = set()
    uniq_items: list[dict[str, str]] = []
    for it in items:
        key = (it.get("category"), it.get("name"))
        if key in seen:
            continue
        seen.add(key)
        uniq_items.append(it)

    if not uniq_items:
        return _guess_from_filename(image_path, color)

    return {"items": uniq_items, "labels": sorted(set(labels)), "source": "model"}

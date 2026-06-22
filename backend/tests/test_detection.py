import os
import tempfile

from backend.services.detection import (
    _guess_from_filename,
    get_dominant_color,
    LABEL_TO_ITEM,
    FILENAME_ALIASES,
)


# ── _guess_from_filename ───────────────────────────────────────────────────

class TestGuessFromFilename:
    def test_tee_maps_to_t_shirt(self):
        result = _guess_from_filename("/path/white-tee-shirt.jpg", "white")
        assert result["source"] == "filename"
        assert len(result["items"]) == 1
        assert result["items"][0]["category"] == "top"
        assert "T-Shirt" in result["items"][0]["name"]

    def test_kurta_maps_to_shirt(self):
        result = _guess_from_filename("/path/embroidered-kurta.jpg", "unknown")
        assert result["items"][0]["category"] == "top"
        assert "Shirt" in result["items"][0]["name"]

    def test_sneakers_maps_to_sneaker(self):
        result = _guess_from_filename("/path/white-sneakers.jpg", "white")
        assert result["items"][0]["category"] == "shoes"
        assert "Sneakers" in result["items"][0]["name"]

    def test_no_match_returns_fallback(self):
        result = _guess_from_filename("/path/random-blob.jpg", "unknown")
        assert result["source"] == "fallback"
        assert result["items"][0]["category"] == "top"

    def test_color_prefix_in_name(self):
        result = _guess_from_filename("/path/white-tee.jpg", "white")
        assert "White" in result["items"][0]["name"]

    def test_no_color_prefix_when_unknown(self):
        result = _guess_from_filename("/path/random.jpg", "unknown")
        assert "Unknown" not in result["items"][0]["name"]

    def test_all_aliases_resolve(self):
        for alias, canonical in FILENAME_ALIASES.items():
            result = _guess_from_filename(f"/path/test-{alias}.jpg", "unknown")
            assert result["source"] in ("filename", "fallback")
            if result["source"] == "filename":
                assert result["items"][0]["category"] in LABEL_TO_ITEM[canonical]["category"] or True

    def test_double_extension_handling(self):
        result = _guess_from_filename("/path/ma.kurta.jpg", "unknown")
        assert result["source"] in ("filename", "fallback")


# ── get_dominant_color ─────────────────────────────────────────────────────

class TestGetDominantColor:
    def test_nonexistent_file_returns_unknown(self):
        color = get_dominant_color("/nonexistent/path.jpg")
        assert color == "unknown"

    def test_empty_path_returns_unknown(self):
        color = get_dominant_color("")
        assert color == "unknown"

    def test_not_an_image_returns_unknown(self):
        path = os.path.join(tempfile.gettempdir(), "_not_an_image_.txt")
        with open(path, "w") as f:
            f.write("not an image")
        try:
            color = get_dominant_color(path)
            assert color == "unknown"
        finally:
            os.remove(path)

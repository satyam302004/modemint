import json
import os
import tempfile
import pytest

from backend.utils.data_loader import load_json, save_json


# ── load_json ──────────────────────────────────────────────────────────────

def test_load_json_missing_file_returns_empty_list():
    path = os.path.join(tempfile.gettempdir(), "_nonexistent_test_file_.json")
    if os.path.exists(path):
        os.remove(path)
    result = load_json(path, [])
    assert result == []


def test_load_json_missing_file_custom_fallback():
    path = os.path.join(tempfile.gettempdir(), "_nonexistent_custom_.json")
    result = load_json(path, {"fallback": True})
    assert result == {"fallback": True}


def test_load_json_missing_file_no_fallback_returns_empty_list():
    path = os.path.join(tempfile.gettempdir(), "_nonexistent_noarg_.json")
    result = load_json(path)
    assert result == []


def test_load_json_falsy_fallback_is_replaced():
    path = os.path.join(tempfile.gettempdir(), "_falsy_fallback_.json")
    result = load_json(path, fallback=None)
    assert result == []


def test_load_json_valid_file():
    path = os.path.join(tempfile.gettempdir(), "_valid_test_.json")
    data = [{"id": 1}, {"id": 2}]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        result = load_json(path, [])
        assert result == data
    finally:
        os.remove(path)


def test_load_json_empty_file():
    path = os.path.join(tempfile.gettempdir(), "_empty_test_.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write("")
    try:
        with pytest.raises(json.JSONDecodeError):
            load_json(path, [])
    finally:
        os.remove(path)


def test_load_json_corrupt_file():
    path = os.path.join(tempfile.gettempdir(), "_corrupt_test_.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write('{"broken": ')
    try:
        with pytest.raises(json.JSONDecodeError):
            load_json(path, [])
    finally:
        os.remove(path)


def test_load_json_wrong_type_returns_non_list():
    path = os.path.join(tempfile.gettempdir(), "_wrong_type_.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"key": "value"}, f)
    try:
        result = load_json(path, [])
        assert isinstance(result, dict)
        assert result["key"] == "value"
    finally:
        os.remove(path)


# ── save_json ──────────────────────────────────────────────────────────────

def test_save_and_reload():
    path = os.path.join(tempfile.gettempdir(), "_save_reload_.json")
    data = [{"a": 1}, {"b": 2}]
    try:
        save_json(path, data)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_save_json_creates_parent_dirs():
    deep_dir = os.path.join(tempfile.gettempdir(), "a", "b", "c")
    path = os.path.join(deep_dir, "_deep_save_.json")
    data = ["test"]
    try:
        save_json(path, data)
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == data
    finally:
        if os.path.exists(path):
            os.remove(path)
        for d in ["c", "b", "a"]:
            p = os.path.join(tempfile.gettempdir(), d)
            if os.path.isdir(p):
                os.rmdir(p) if not os.listdir(p) else None


def test_save_json_overwrites_existing():
    path = os.path.join(tempfile.gettempdir(), "_overwrite_test_.json")
    try:
        save_json(path, ["old"])
        save_json(path, ["new"])
        with open(path, "r", encoding="utf-8") as f:
            assert json.load(f) == ["new"]
    finally:
        if os.path.exists(path):
            os.remove(path)


def test_save_json_unicode_roundtrip():
    path = os.path.join(tempfile.gettempdir(), "_unicode_test_.json")
    data = ["\u20b9", "\u00e9", "\u4e2d\u6587"]
    try:
        save_json(path, data)
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data
    finally:
        if os.path.exists(path):
            os.remove(path)

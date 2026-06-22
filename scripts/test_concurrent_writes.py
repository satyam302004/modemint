"""
Concurrent write test for ModeMint's JSON persistence.

Launches N simultaneous requests to POST/DELETE endpoints
and checks for data loss or corruption.

Usage:
    python scripts/test_concurrent_writes.py [--concurrency 10]

Requires the Flask server to be running on http://127.0.0.1:5000.
"""
import json
import sys
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

BASE = "http://127.0.0.1:5000"


def post_wardrobe(name, category):
    try:
        r = requests.post(
            f"{BASE}/wardrobe",
            json={"name": name, "category": category, "color": "test", "style": "casual", "occasion": "casual"},
            timeout=10,
        )
        return ("post", r.status_code, r.json() if r.ok else None)
    except Exception as e:
        return ("post", 0, str(e))


def post_favorite(name):
    try:
        r = requests.post(
            f"{BASE}/favorites",
            json={"name": name, "outfit": {"items": {}, "total_price": 0, "score": 0, "trend_score": 0, "reasons": []}},
            timeout=10,
        )
        return ("post", r.status_code, r.json() if r.ok else None)
    except Exception as e:
        return ("post", 0, str(e))


def delete_item(endpoint, item_id):
    try:
        r = requests.delete(f"{BASE}{endpoint}/{item_id}", timeout=10)
        return ("delete", r.status_code, r.json() if r.ok else None)
    except Exception as e:
        return ("delete", 0, str(e))


def run_test(label, concurrency, fn_create, fn_get, fn_delete_getter=None):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"{'='*60}")

    # Step 1: Create items concurrently
    print(f"\nCreating {concurrency} items concurrently...")
    created_ids = []

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(fn_create, f"Item-{i}", "top") for i in range(concurrency)]
        for f in as_completed(futures):
            action, status, data = f.result()
            if status == 201 and data and "id" in data:
                created_ids.append(data["id"])
            elif status != 201:
                print(f"  FAIL: Create returned {status} - {data}")

    print(f"  Created {len(created_ids)} items (expected {concurrency})")

    # Step 2: Verify count via GET
    r = fn_get()
    if r.status_code == 200:
        actual_count = len(r.json())
        print(f"  GET count: {actual_count} (expected ~{concurrency})")
        if actual_count < concurrency * 0.9:
            print(f"  WARNING: Significant data loss! Expected ~{concurrency}, got {actual_count}")
    else:
        print(f"  FAIL: GET returned {r.status_code}")

    # Step 3: Delete concurrently
    if fn_delete_getter and created_ids:
        print(f"\nDeleting {len(created_ids)} items concurrently...")
        deleted = 0
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(fn_delete_getter, item_id) for item_id in created_ids]
            for f in as_completed(futures):
                action, status, data = f.result()
                if status == 200:
                    deleted += 1
        print(f"  Deleted {deleted} items (expected {len(created_ids)})")

        # Step 4: Verify empty
        r = fn_get()
        if r.status_code == 200:
            remaining = len(r.json())
            print(f"  Items remaining after delete: {remaining}")
            if remaining > 0:
                print(f"  WARNING: {remaining} items still present after delete")

    return created_ids


def main():
    parser = argparse.ArgumentParser(description="Concurrent write test for ModeMint")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent requests")
    args = parser.parse_args()

    print("=" * 60)
    print("ModeMint Concurrent Write Test")
    print(f"Concurrency level: {args.concurrency}")
    print(f"Server: {BASE}")
    print("=" * 60)

    # Health check
    try:
        r = requests.get(f"{BASE}/meta", timeout=5)
        print(f"\nServer health: OK ({r.status_code})")
    except Exception as e:
        print(f"\nServer not reachable: {e}")
        print("Start the Flask server first: python -m backend.app")
        sys.exit(1)

    # Test 1: Wardrobe POST concurrency
    run_test(
        "Wardrobe Concurrent POST",
        args.concurrency,
        post_wardrobe,
        lambda: requests.get(f"{BASE}/wardrobe", timeout=10),
        lambda item_id: delete_item("/wardrobe", item_id),
    )

    # Test 2: Favorites POST concurrency
    run_test(
        "Favorites Concurrent POST",
        args.concurrency,
        lambda name, _: post_favorite(name),
        lambda: requests.get(f"{BASE}/favorites", timeout=10),
        lambda item_id: delete_item("/favorites", item_id),
    )

    print(f"\n{'='*60}")
    print("TEST COMPLETE")
    print("Review any WARNING messages above for data loss indicators.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

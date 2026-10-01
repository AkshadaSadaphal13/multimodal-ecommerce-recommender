"""Smoke tests for a running local API. Set API_BASE_URL to override localhost."""
import os
from pathlib import Path
import requests

BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
queries = ["black shoes", "black running shoes", "white sneakers", "women sandals",
           "wireless headphones", "beauty cleanser", "gaming controller", "face moisturizer"]
health = requests.get(f"{BASE}/health", timeout=10)
assert health.status_code == 200 and health.json().get("status")
for query in queries:
    response = requests.post(f"{BASE}/api/recommend", json={"query": query, "top_k": 5}, timeout=120)
    assert response.status_code == 200, f"text search {query!r}: {response.text}"
    assert isinstance(response.json().get("results"), list)
filtered = requests.post(f"{BASE}/api/recommend", json={"query": "cleanser", "top_k": 5, "category": "All Beauty", "min_rating": 4, "max_price": 50}, timeout=120)
assert filtered.status_code == 200 and isinstance(filtered.json().get("results"), list)
assert requests.get(f"{BASE}/api/products/", timeout=20).status_code == 200

image_path = Path(os.getenv("TEST_IMAGE", "data/images"))
images = [image_path] if image_path.is_file() else list(image_path.rglob("*.jpg")) + list(image_path.rglob("*.png")) if image_path.exists() else []
if not images:
    print("SKIP image and multimodal API checks: no local JPG/PNG fixture found")
else:
    with images[0].open("rb") as stream:
        image_response = requests.post(f"{BASE}/api/recommend/image", files={"image": (images[0].name, stream)}, data={"top_k": 5}, timeout=180)
    assert image_response.status_code == 200, image_response.text
    assert isinstance(image_response.json().get("results"), list)
    with images[0].open("rb") as stream:
        multi_response = requests.post(f"{BASE}/api/recommend/multimodal", files={"image": (images[0].name, stream)}, data={"query": "product", "top_k": 5}, timeout=180)
    assert multi_response.status_code == 200, multi_response.text
    assert isinstance(multi_response.json().get("results"), list)
print("API smoke tests passed")

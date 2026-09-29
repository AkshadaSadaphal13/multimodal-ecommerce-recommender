import gzip
import json
from pathlib import Path

import pandas as pd


def load_reviews(
    reviews_path: str | Path,
    valid_product_ids: set,
    max_reviews: int = 50000
) -> pd.DataFrame:

    reviews_path = Path(reviews_path)

    if not reviews_path.exists():
        raise FileNotFoundError(
            f"Reviews file not found: {reviews_path}"
        )

    records = []

    with gzip.open(
        reviews_path,
        "rt",
        encoding="utf-8"
    ) as file:

        for line in file:

            if len(records) >= max_reviews:
                break

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            product_id = (
                item.get("parent_asin")
                or item.get("asin")
            )

            if product_id not in valid_product_ids:
                continue

            review_text = str(
                item.get("text", "")
            ).strip()

            if not review_text:
                continue

            rating = item.get("rating")

            try:
                rating = float(rating)
            except (ValueError, TypeError):
                continue

            if not 1 <= rating <= 5:
                continue

            records.append({
                "review_id": item.get(
                    "review_id",
                    f"{item.get('user_id', '')}_{item.get('timestamp', '')}"
                ),
                "product_id": product_id,
                "user_id": item.get("user_id", ""),
                "rating": rating,
                "review_title": str(
                    item.get("title", "")
                ).strip(),
                "review_text": review_text,
                "timestamp": item.get("timestamp"),
                "verified_purchase": item.get(
                    "verified_purchase",
                    False
                ),
                "helpful_vote": item.get(
                    "helpful_vote",
                    0
                ),
            })

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(
            "No valid reviews were found "
            "for the selected products."
        )

    df = df.drop_duplicates(
        subset=[
            "product_id",
            "user_id",
            "review_text"
        ]
    )

    return df.reset_index(drop=True)
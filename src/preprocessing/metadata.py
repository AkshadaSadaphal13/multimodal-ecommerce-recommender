import gzip
import json
from pathlib import Path

import pandas as pd


def _safe_text(value):
    """
    Convert list/string/None into clean text.
    """
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(
            str(item).strip()
            for item in value
            if item is not None
        )

    return str(value).strip()


def _extract_image_url(images):
    """
    Extract the best available product image URL.
    Amazon metadata can contain multiple image resolutions.
    """
    if not isinstance(images, list) or not images:
        return ""

    for image in images:
        if not isinstance(image, dict):
            continue

        # Prefer large/high-resolution image fields.
        for key in ["large", "hi_res", "thumb"]:
            url = image.get(key)

            if url:
                return str(url)

    return ""


def _extract_brand(store, details):
    """
    Try to obtain a brand/store value from available metadata.
    """
    if store:
        return str(store).strip()

    if isinstance(details, dict):
        for key, value in details.items():
            if "brand" in str(key).lower():
                return _safe_text(value)

    return ""


def load_metadata(
    metadata_path: str | Path,
    max_products: int = 5000
) -> pd.DataFrame:

    metadata_path = Path(metadata_path)

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Metadata file not found: {metadata_path}"
        )

    records = []

    with gzip.open(metadata_path, "rt", encoding="utf-8") as file:

        for line in file:

            if len(records) >= max_products:
                break

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            product_id = (
                item.get("parent_asin")
                or item.get("asin")
            )

            title = _safe_text(item.get("title"))

            if not product_id or not title:
                continue

            description = _safe_text(
                item.get("description")
            )

            features = _safe_text(
                item.get("features")
            )

            categories = _safe_text(
                item.get("categories")
            )

            store = _safe_text(
                item.get("store")
            )

            details = item.get("details", {})

            brand = _extract_brand(
                store,
                details
            )

            image_url = _extract_image_url(
                item.get("images")
            )

            price = item.get("price")

            try:
                price = float(price) if price is not None else None
            except (ValueError, TypeError):
                price = None

            average_rating = item.get(
                "average_rating"
            )

            rating_number = item.get(
                "rating_number"
            )

            try:
                average_rating = (
                    float(average_rating)
                    if average_rating is not None
                    else None
                )
            except (ValueError, TypeError):
                average_rating = None

            try:
                rating_number = (
                    int(rating_number)
                    if rating_number is not None
                    else 0
                )
            except (ValueError, TypeError):
                rating_number = 0

            combined_text = " ".join(
                part
                for part in [
                    title,
                    features,
                    description
                ]
                if part
            )

            records.append({
                "product_id": product_id,
                "title": title,
                "category": categories,
                "brand": brand,
                "price": price,
                "average_rating": average_rating,
                "rating_number": rating_number,
                "features": features,
                "description": description,
                "combined_text": combined_text,
                "image_url": image_url,
            })

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(
            "No valid product records were found."
        )

    df = df.drop_duplicates(
        subset=["product_id"]
    )

    df = df.reset_index(drop=True)

    return df
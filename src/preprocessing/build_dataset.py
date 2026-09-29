from pathlib import Path

from src.config import (
    METADATA_FILE,
    REVIEWS_FILE,
    PROCESSED_DIR,
    MAX_PRODUCTS,
    MAX_REVIEWS,
)

from src.preprocessing.metadata import load_metadata
from src.preprocessing.reviews import load_reviews
from src.preprocessing.interactions import build_interactions


def main():

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 60)
    print("MULTIMODAL E-COMMERCE DATA PIPELINE")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Metadata
    # --------------------------------------------------

    print("\n[1/4] Loading product metadata...")

    products = load_metadata(
        METADATA_FILE,
        max_products=MAX_PRODUCTS
    )

    print(
        f"Products loaded: {len(products):,}"
    )

    # --------------------------------------------------
    # 2. Reviews
    # --------------------------------------------------

    print("\n[2/4] Loading reviews...")

    valid_product_ids = set(
        products["product_id"]
    )

    reviews = load_reviews(
        REVIEWS_FILE,
        valid_product_ids,
        max_reviews=MAX_REVIEWS
    )

    print(
        f"Reviews loaded: {len(reviews):,}"
    )

    # --------------------------------------------------
    # 3. Interactions
    # --------------------------------------------------

    print("\n[3/4] Creating interactions...")

    interactions = build_interactions(
        reviews
    )

    # --------------------------------------------------
    # 4. Users
    # --------------------------------------------------

    users = pd.DataFrame({
        "user_id": reviews[
            "user_id"
        ].dropna().unique()
    })

    # --------------------------------------------------
    # Save
    # --------------------------------------------------

    print("\n[4/4] Saving processed datasets...")

    products.to_csv(
        PROCESSED_DIR / "products.csv",
        index=False
    )

    reviews.to_csv(
        PROCESSED_DIR / "reviews.csv",
        index=False
    )

    interactions.to_csv(
        PROCESSED_DIR / "interactions.csv",
        index=False
    )

    users.to_csv(
        PROCESSED_DIR / "users.csv",
        index=False
    )

    print("\n" + "=" * 60)
    print("DATASET CREATED SUCCESSFULLY")
    print("=" * 60)

    print(
        f"Products     : {len(products):,}"
    )
    print(
        f"Reviews      : {len(reviews):,}"
    )
    print(
        f"Users        : {len(users):,}"
    )
    print(
        f"Interactions : {len(interactions):,}"
    )

    print("\nFiles:")
    print(PROCESSED_DIR / "products.csv")
    print(PROCESSED_DIR / "reviews.csv")
    print(PROCESSED_DIR / "users.csv")
    print(PROCESSED_DIR / "interactions.csv")


if __name__ == "__main__":
    import pandas as pd

    main()
import os
import json
import requests
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

PRODUCT_FILE = "data/processed/products_aligned.csv"
OUTPUT_FILE = "data/processed/reviews_multicategory.csv"

MAX_REVIEWS_PER_PRODUCT = 5

BASE_URL = (
    "https://huggingface.co/datasets/"
    "McAuley-Lab/Amazon-Reviews-2023/"
    "resolve/main/"
    "raw/review_categories/"
)

CATEGORIES = {
    "All_Beauty": "All Beauty",
    "Digital_Music": "Digital Music",
    "Gift_Cards": "Gift Cards",
    "Health_and_Personal_Care": "Health & Personal Care",
    "Video_Games": "Video Games",
}


# ============================================================
# LOAD PRODUCTS
# ============================================================

print("=" * 70)
print("BUILDING MULTI-CATEGORY REVIEW DATASET")
print("=" * 70)

print("\nLoading selected products...")

products = pd.read_csv(PRODUCT_FILE)

products["product_id"] = (
    products["product_id"]
    .astype(str)
    .str.strip()
)

print(f"Products: {len(products)}")

for category in CATEGORIES.values():

    count = (
        products["main_category"] == category
    ).sum()

    print(f"{category}: {count} products")


# ============================================================
# CREATE PRODUCT ID SETS
# ============================================================

product_ids_by_category = {}

for hf_category, display_category in CATEGORIES.items():

    category_products = products[
        products["main_category"] == display_category
    ]

    product_ids_by_category[hf_category] = set(
        category_products["product_id"]
        .astype(str)
        .str.strip()
        .tolist()
    )


# ============================================================
# DOWNLOAD / STREAM JSONL
# ============================================================

all_reviews = []

for hf_category, display_category in CATEGORIES.items():

    print("\n" + "=" * 70)
    print(f"PROCESSING REVIEWS: {display_category}")
    print("=" * 70)

    target_product_ids = product_ids_by_category[hf_category]

    print(
        f"Target products: "
        f"{len(target_product_ids)}"
    )

    filename = f"{hf_category}.jsonl"

    url = BASE_URL + filename

    print("\nSource:")
    print(url)

    print("\nConnecting to Hugging Face...")

    try:

        response = requests.get(
            url,
            stream=True,
            timeout=60
        )

        response.raise_for_status()

    except Exception as e:

        print("\nERROR downloading review file:")
        print(e)

        continue

    print("Connection successful.")
    print("Streaming reviews...")

    review_counts = {}

    processed = 0
    matched = 0

    # --------------------------------------------------------
    # Read JSONL line by line
    # --------------------------------------------------------

    for line in response.iter_lines(
        decode_unicode=True
    ):

        if not line:
            continue

        processed += 1

        try:

            review = json.loads(line)

        except json.JSONDecodeError:

            continue

        # ----------------------------------------------------
        # Product ID
        # ----------------------------------------------------

        product_id = review.get("parent_asin")

        if product_id is None:
            continue

        product_id = str(product_id).strip()

        # ----------------------------------------------------
        # Match our selected products
        # ----------------------------------------------------

        if product_id not in target_product_ids:
            continue

        # ----------------------------------------------------
        # Maximum reviews per product
        # ----------------------------------------------------

        current_count = review_counts.get(
            product_id,
            0
        )

        if current_count >= MAX_REVIEWS_PER_PRODUCT:
            continue

        # ----------------------------------------------------
        # Review text
        # ----------------------------------------------------

        review_text = review.get("text")

        if review_text is None:
            continue

        review_text = str(review_text).strip()

        if not review_text:
            continue

        # ----------------------------------------------------
        # Review title
        # ----------------------------------------------------

        review_title = review.get(
            "title",
            ""
        )

        if review_title is None:
            review_title = ""

        review_title = str(
            review_title
        ).strip()

        # ----------------------------------------------------
        # Other fields
        # ----------------------------------------------------

        rating = review.get("rating")

        user_id = review.get("user_id")

        if user_id is not None:
            user_id = str(user_id)

        timestamp = review.get(
            "timestamp"
        )

        helpful_vote = review.get(
            "helpful_vote",
            0
        )

        verified_purchase = review.get(
            "verified_purchase",
            False
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        all_reviews.append(
            {
                "product_id": product_id,
                "rating": rating,
                "review_title": review_title,
                "review_text": review_text,
                "user_id": user_id,
                "timestamp": timestamp,
                "helpful_vote": helpful_vote,
                "verified_purchase": verified_purchase,
                "main_category": display_category,
            }
        )

        review_counts[product_id] = (
            current_count + 1
        )

        matched += 1

        # ----------------------------------------------------
        # Progress
        # ----------------------------------------------------

        if matched % 100 == 0:

            print(
                f"Matched reviews: {matched} | "
                f"Products covered: "
                f"{len(review_counts)}"
            )

        # ----------------------------------------------------
        # Stop when every product has enough reviews
        # ----------------------------------------------------

        if (
            len(review_counts)
            == len(target_product_ids)
            and all(
                count >= MAX_REVIEWS_PER_PRODUCT
                for count in review_counts.values()
            )
        ):

            print(
                "\nAll selected products have "
                f"{MAX_REVIEWS_PER_PRODUCT} reviews."
            )

            break

    response.close()

    print("\nCategory complete.")

    print(
        f"Reviews processed: {processed}"
    )

    print(
        f"Matched reviews: {matched}"
    )

    print(
        f"Products with reviews: "
        f"{len(review_counts)}"
    )


# ============================================================
# SAVE
# ============================================================

print("\n" + "=" * 70)
print("REVIEW DATASET CREATION COMPLETE")
print("=" * 70)

columns = [
    "product_id",
    "rating",
    "review_title",
    "review_text",
    "user_id",
    "timestamp",
    "helpful_vote",
    "verified_purchase",
    "main_category",
]

if len(all_reviews) == 0:

    print("\nWARNING: No reviews were collected.")

    pd.DataFrame(
        columns=columns
    ).to_csv(
        OUTPUT_FILE,
        index=False
    )

else:

    reviews_df = pd.DataFrame(
        all_reviews
    )

    reviews_df = reviews_df.drop_duplicates(
        subset=[
            "product_id",
            "user_id",
            "timestamp",
            "review_text",
        ]
    )

    reviews_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nTotal reviews: "
        f"{len(reviews_df)}"
    )

    print(
        f"Unique products: "
        f"{reviews_df['product_id'].nunique()}"
    )

    print("\nReviews by category:")

    print(
        reviews_df[
            "main_category"
        ].value_counts()
    )

    print("\nSample reviews:")

    print(
        reviews_df
        .head(5)
        .to_string(index=False)
    )

print("\nSaved to:")
print(
    os.path.abspath(
        OUTPUT_FILE
    )
)

print("\n" + "=" * 70)
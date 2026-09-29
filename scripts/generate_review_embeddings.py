from pathlib import Path

import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# NEW: use the newly generated multicategory sentiment dataset
REVIEWS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "reviews_multicategory_sentiment.csv"
)

PRODUCTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_aligned.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REVIEW_EMBEDDINGS_PATH = (
    OUTPUT_DIR
    / "review_embeddings.npy"
)

REVIEW_PRODUCT_IDS_PATH = (
    OUTPUT_DIR
    / "review_product_ids.csv"
)


# ============================================================
# SETTINGS
# ============================================================

MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)

BATCH_SIZE = 32


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("GENERATING PRODUCT REVIEW EMBEDDINGS")
print("=" * 70)


# ============================================================
# CHECK INPUT FILES
# ============================================================

if not REVIEWS_PATH.exists():

    raise FileNotFoundError(
        f"\nReview file not found:\n{REVIEWS_PATH}"
    )

if not PRODUCTS_PATH.exists():

    raise FileNotFoundError(
        f"\nProduct file not found:\n{PRODUCTS_PATH}"
    )


# ============================================================
# LOAD DATA
# ============================================================

print()
print("Loading reviews...")

reviews = pd.read_csv(
    REVIEWS_PATH
)

print(
    "Loading products..."
)

products = pd.read_csv(
    PRODUCTS_PATH
)

print()
print(
    "Reviews:",
    len(reviews)
)

print(
    "Products:",
    len(products)
)


# ============================================================
# CHECK REQUIRED PRODUCT ID COLUMN
# ============================================================

if "product_id" not in reviews.columns:

    raise ValueError(
        "Review dataset does not contain "
        "'product_id' column."
    )

if "product_id" not in products.columns:

    raise ValueError(
        "Product dataset does not contain "
        "'product_id' column."
    )


# ============================================================
# DETECT REVIEW TEXT COLUMN
# ============================================================

review_text_column = None

for column in [
    "review_text",
    "text",
    "review",
    "body",
    "content"
]:

    if column in reviews.columns:

        review_text_column = column
        break


if review_text_column is None:

    raise ValueError(
        "Could not find review text column.\n"
        "Expected one of:\n"
        "review_text, text, review, body, content"
    )


print()
print(
    "Review text column:",
    review_text_column
)


# ============================================================
# CLEAN PRODUCT IDS
# ============================================================

reviews["product_id"] = (
    reviews["product_id"]
    .astype(str)
    .str.strip()
)

products["product_id"] = (
    products["product_id"]
    .astype(str)
    .str.strip()
)


# ============================================================
# KEEP ONLY OUR PRODUCTS
# ============================================================

valid_product_ids = set(
    products["product_id"]
)

reviews = reviews[
    reviews["product_id"].isin(
        valid_product_ids
    )
].copy()

print()
print(
    "Reviews matching our products:",
    len(reviews)
)


# ============================================================
# CLEAN REVIEW TEXT
# ============================================================

reviews[review_text_column] = (
    reviews[review_text_column]
    .fillna("")
    .astype(str)
    .str.strip()
)

reviews = reviews[
    reviews[review_text_column].str.len() > 0
].copy()

print(
    "Reviews with valid text:",
    len(reviews)
)


# ============================================================
# CHECK REVIEWS
# ============================================================

if len(reviews) == 0:

    raise ValueError(
        "No valid reviews available "
        "for embedding generation."
    )


print(
    "Unique products with reviews:",
    reviews["product_id"].nunique()
)


# ============================================================
# LOAD SENTENCE-BERT
# ============================================================

print()
print("Loading SBERT...")

model = SentenceTransformer(
    MODEL_NAME
)

print(
    "SBERT loaded."
)


# ============================================================
# CREATE PRODUCT REVIEW EMBEDDINGS
# ============================================================

product_ids = []
product_embeddings = []

grouped = reviews.groupby(
    "product_id"
)

total_products = len(grouped)

print()
print(
    "Products with reviews:",
    total_products
)

print()
print(
    "Generating review embeddings..."
)


for counter, (
    product_id,
    group
) in enumerate(
    grouped,
    start=1
):

    # --------------------------------------------------------
    # Get all reviews for this product
    # --------------------------------------------------------

    review_texts = (
        group[
            review_text_column
        ]
        .tolist()
    )

    # --------------------------------------------------------
    # Generate SBERT embeddings
    # --------------------------------------------------------

    embeddings = model.encode(
        review_texts,
        batch_size=BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False
    ).astype(
        np.float32
    )

    # --------------------------------------------------------
    # Aggregate all reviews for this product
    # --------------------------------------------------------

    product_embedding = np.mean(
        embeddings,
        axis=0
    )

    # --------------------------------------------------------
    # Normalize product embedding
    # --------------------------------------------------------

    norm = np.linalg.norm(
        product_embedding
    )

    if norm > 0:

        product_embedding = (
            product_embedding / norm
        )

    # --------------------------------------------------------
    # Store
    # --------------------------------------------------------

    product_ids.append(
        product_id
    )

    product_embeddings.append(
        product_embedding
    )

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    if (
        counter % 100 == 0
        or counter == total_products
    ):

        print(
            f"Processed "
            f"{counter}/{total_products}"
        )


# ============================================================
# CONVERT TO NUMPY
# ============================================================

product_embeddings = np.asarray(
    product_embeddings,
    dtype=np.float32
)


# ============================================================
# FINAL NORMALIZATION
# ============================================================

print()
print(
    "Normalizing final product embeddings..."
)

norms = np.linalg.norm(
    product_embeddings,
    axis=1,
    keepdims=True
)

norms[norms == 0] = 1.0

product_embeddings = (
    product_embeddings / norms
).astype(
    np.float32
)


# ============================================================
# SAVE EMBEDDINGS
# ============================================================

print()
print(
    "Saving review embeddings..."
)

np.save(
    REVIEW_EMBEDDINGS_PATH,
    product_embeddings
)

pd.DataFrame(
    {
        "product_id": product_ids
    }
).to_csv(
    REVIEW_PRODUCT_IDS_PATH,
    index=False
)


# ============================================================
# VERIFY SAVED DATA
# ============================================================

saved_embeddings = np.load(
    REVIEW_EMBEDDINGS_PATH
)

saved_product_ids = pd.read_csv(
    REVIEW_PRODUCT_IDS_PATH
)


# ============================================================
# REPORT
# ============================================================

print()
print("=" * 70)
print("REVIEW EMBEDDINGS COMPLETE")
print("=" * 70)

print()

print(
    "Products with review embeddings:",
    len(product_ids)
)

print(
    "Embedding shape:",
    product_embeddings.shape
)

print(
    "Expected dimension:",
    384
)

print(
    "Embedding dtype:",
    product_embeddings.dtype
)

print()

print(
    "Saved embeddings shape:",
    saved_embeddings.shape
)

print(
    "Saved product IDs:",
    len(saved_product_ids)
)

print()

print(
    "First embedding:"
)

print(
    product_embeddings[0][:10]
)

print()

print(
    "First embedding norm:",
    np.linalg.norm(
        product_embeddings[0]
    )
)

print()

print(
    "Saved:"
)

print(
    REVIEW_EMBEDDINGS_PATH
)

print(
    REVIEW_PRODUCT_IDS_PATH
)

print()
print("=" * 70)
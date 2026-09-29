from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

PROCESSED_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
)


# ------------------------------------------------------------
# Input files
# ------------------------------------------------------------

TEXT_EMBEDDINGS_PATH = (
    EMBEDDING_DIR
    / "text_embeddings.npy"
)

TEXT_IDS_PATH = (
    EMBEDDING_DIR
    / "text_product_ids.csv"
)

IMAGE_EMBEDDINGS_PATH = (
    EMBEDDING_DIR
    / "image_embeddings.npy"
)

IMAGE_IDS_PATH = (
    EMBEDDING_DIR
    / "image_product_ids.csv"
)

PRODUCTS_PATH = (
    PROCESSED_DIR
    / "products_multimodal.csv"
)


# ------------------------------------------------------------
# Output files
# ------------------------------------------------------------

ALIGNED_TEXT_PATH = (
    EMBEDDING_DIR
    / "aligned_text_embeddings.npy"
)

ALIGNED_IMAGE_PATH = (
    EMBEDDING_DIR
    / "aligned_image_embeddings.npy"
)

ALIGNED_IDS_PATH = (
    EMBEDDING_DIR
    / "aligned_product_ids.csv"
)

ALIGNED_PRODUCTS_PATH = (
    PROCESSED_DIR
    / "products_aligned.csv"
)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("ALIGNING TEXT AND IMAGE EMBEDDINGS")
print("=" * 70)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

print()
print("Loading text embeddings...")

text_embeddings = np.load(
    TEXT_EMBEDDINGS_PATH
)

print(
    "Text embedding shape:",
    text_embeddings.shape
)


print()
print("Loading image embeddings...")

image_embeddings = np.load(
    IMAGE_EMBEDDINGS_PATH
)

print(
    "Image embedding shape:",
    image_embeddings.shape
)


# ============================================================
# LOAD PRODUCT IDS
# ============================================================

print()
print("Loading text product IDs...")

text_ids_df = pd.read_csv(
    TEXT_IDS_PATH
)

print(
    "Text IDs:",
    len(text_ids_df)
)


print()
print("Loading image product IDs...")

image_ids_df = pd.read_csv(
    IMAGE_IDS_PATH
)

print(
    "Image IDs:",
    len(image_ids_df)
)


# ============================================================
# VALIDATE
# ============================================================

if len(text_embeddings) != len(text_ids_df):

    raise ValueError(
        "Text embedding count does not match "
        "text product ID count."
    )


if len(image_embeddings) != len(image_ids_df):

    raise ValueError(
        "Image embedding count does not match "
        "image product ID count."
    )


# ============================================================
# CREATE ID → EMBEDDING MAPPINGS
# ============================================================

print()
print("Creating product ID mappings...")


text_id_to_index = {
    str(product_id): index
    for index, product_id
    in enumerate(
        text_ids_df["product_id"]
    )
}


image_id_to_index = {
    str(product_id): index
    for index, product_id
    in enumerate(
        image_ids_df["product_id"]
    )
}


# ============================================================
# FIND COMMON PRODUCTS
# ============================================================

text_product_ids = set(
    text_id_to_index.keys()
)

image_product_ids = set(
    image_id_to_index.keys()
)


common_ids = (
    text_product_ids
    & image_product_ids
)


print()
print(
    "Text products:",
    len(text_product_ids)
)

print(
    "Image products:",
    len(image_product_ids)
)

print(
    "Common products:",
    len(common_ids)
)


if len(common_ids) == 0:

    raise RuntimeError(
        "No common product IDs found."
    )


# ============================================================
# PRESERVE TEXT DATASET ORDER
# ============================================================

ordered_common_ids = [
    str(product_id)
    for product_id
    in text_ids_df["product_id"]
    if str(product_id)
    in common_ids
]


# ============================================================
# CREATE ALIGNED ARRAYS
# ============================================================

print()
print("Creating aligned embeddings...")


text_indices = [
    text_id_to_index[
        product_id
    ]
    for product_id
    in ordered_common_ids
]


image_indices = [
    image_id_to_index[
        product_id
    ]
    for product_id
    in ordered_common_ids
]


aligned_text = (
    text_embeddings[
        text_indices
    ]
)


aligned_image = (
    image_embeddings[
        image_indices
    ]
)


# ============================================================
# VALIDATE ALIGNMENT
# ============================================================

if len(aligned_text) != len(
    aligned_image
):

    raise RuntimeError(
        "Aligned text and image "
        "embedding counts do not match."
    )


print()
print(
    "Aligned text shape:",
    aligned_text.shape
)

print(
    "Aligned image shape:",
    aligned_image.shape
)


# ============================================================
# SAVE ALIGNED EMBEDDINGS
# ============================================================

print()
print("Saving aligned embeddings...")


np.save(
    ALIGNED_TEXT_PATH,
    aligned_text.astype(
        np.float32
    )
)


np.save(
    ALIGNED_IMAGE_PATH,
    aligned_image.astype(
        np.float32
    )
)


# ============================================================
# SAVE ALIGNED PRODUCT IDs
# ============================================================

aligned_ids_df = pd.DataFrame({
    "product_id":
        ordered_common_ids
})


aligned_ids_df.to_csv(
    ALIGNED_IDS_PATH,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# ALIGN PRODUCT DATASET
# ============================================================

print()
print("Aligning product metadata...")


products_df = pd.read_csv(
    PRODUCTS_PATH
)


products_df["product_id"] = (
    products_df["product_id"]
    .astype(str)
)


aligned_products = (
    products_df[
        products_df["product_id"]
        .isin(common_ids)
    ]
    .copy()
)


# Reorder exactly according to embeddings

aligned_products = (
    aligned_products
    .set_index("product_id")
    .loc[ordered_common_ids]
    .reset_index()
)


aligned_products.to_csv(
    ALIGNED_PRODUCTS_PATH,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("EMBEDDING ALIGNMENT COMPLETE")
print("=" * 70)

print()

print(
    "Common products:",
    len(ordered_common_ids)
)

print()

print(
    "Aligned text embeddings:"
)

print(
    aligned_text.shape
)

print()

print(
    "Aligned image embeddings:"
)

print(
    aligned_image.shape
)

print()

print(
    "Aligned product metadata:"
)

print(
    aligned_products.shape
)

print()

print(
    "Saved:"
)

print(
    ALIGNED_TEXT_PATH
)

print(
    ALIGNED_IMAGE_PATH
)

print(
    ALIGNED_IDS_PATH
)

print(
    ALIGNED_PRODUCTS_PATH
)

print()

print(
    "Category distribution:"
)

print(
    aligned_products[
        "main_category"
    ]
    .value_counts()
    .to_string()
)

print()

print("=" * 70)
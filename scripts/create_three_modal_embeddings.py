from pathlib import Path

import numpy as np
import pandas as pd
import faiss


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EMBEDDINGS_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

INDEX_DIR = (
    PROJECT_ROOT
    / "index"
)

INDEX_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUT FILES
# ============================================================

TEXT_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIR
    / "aligned_text_embeddings.npy"
)

IMAGE_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIR
    / "aligned_image_embeddings.npy"
)

ALIGNED_PRODUCT_IDS_PATH = (
    EMBEDDINGS_DIR
    / "aligned_product_ids.csv"
)

REVIEW_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIR
    / "review_embeddings.npy"
)

REVIEW_PRODUCT_IDS_PATH = (
    EMBEDDINGS_DIR
    / "review_product_ids.csv"
)

TEXT_PROJECTION_PATH = (
    EMBEDDINGS_DIR
    / "text_projection.npy"
)


# ============================================================
# OUTPUT FILES
# ============================================================

OUTPUT_EMBEDDINGS_PATH = (
    EMBEDDINGS_DIR
    / "three_modal_embeddings.npy"
)

OUTPUT_PRODUCT_IDS_PATH = (
    EMBEDDINGS_DIR
    / "three_modal_product_ids.csv"
)

IMAGE_PROJECTION_PATH = (
    EMBEDDINGS_DIR
    / "image_projection.npy"
)

REVIEW_PROJECTION_PATH = (
    EMBEDDINGS_DIR
    / "review_projection.npy"
)

THREE_MODAL_INDEX_PATH = (
    INDEX_DIR
    / "three_modal_product_index.faiss"
)


# ============================================================
# FUSION WEIGHTS
# ============================================================

IMAGE_WEIGHT = 0.4
TEXT_WEIGHT = 0.4
REVIEW_WEIGHT = 0.2

assert abs(
    IMAGE_WEIGHT
    + TEXT_WEIGHT
    + REVIEW_WEIGHT
    - 1.0
) < 1e-6


TARGET_DIMENSION = 256


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("3-MODAL EMBEDDING ALIGNMENT AND FUSION")
print("=" * 70)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

print()
print("Loading embeddings...")

text_embeddings = np.load(
    TEXT_EMBEDDINGS_PATH
).astype(
    np.float32
)

image_embeddings = np.load(
    IMAGE_EMBEDDINGS_PATH
).astype(
    np.float32
)

review_embeddings = np.load(
    REVIEW_EMBEDDINGS_PATH
).astype(
    np.float32
)

aligned_product_ids = pd.read_csv(
    ALIGNED_PRODUCT_IDS_PATH
)["product_id"].astype(
    str
).str.strip().tolist()

review_product_ids = pd.read_csv(
    REVIEW_PRODUCT_IDS_PATH
)["product_id"].astype(
    str
).str.strip().tolist()


print(
    "Text embeddings:",
    text_embeddings.shape
)

print(
    "Image embeddings:",
    image_embeddings.shape
)

print(
    "Review embeddings:",
    review_embeddings.shape
)

print(
    "Text/Image products:",
    len(aligned_product_ids)
)

print(
    "Review products:",
    len(review_product_ids)
)


# ============================================================
# CREATE PRODUCT ID LOOKUPS
# ============================================================

aligned_id_to_index = {
    product_id: index
    for index, product_id
    in enumerate(aligned_product_ids)
}

review_id_to_index = {
    product_id: index
    for index, product_id
    in enumerate(review_product_ids)
}


# ============================================================
# FIND COMMON PRODUCTS
# ============================================================

common_product_ids = [
    product_id
    for product_id in aligned_product_ids
    if product_id in review_id_to_index
]


print()
print(
    "Common products:",
    len(common_product_ids)
)


if len(common_product_ids) == 0:

    raise ValueError(
        "No common products found between "
        "text/image and review embeddings."
    )


# ============================================================
# ALIGN TEXT + IMAGE + REVIEW
# ============================================================

text_indices = [
    aligned_id_to_index[product_id]
    for product_id in common_product_ids
]

review_indices = [
    review_id_to_index[product_id]
    for product_id in common_product_ids
]


aligned_text = text_embeddings[
    text_indices
]

aligned_image = image_embeddings[
    text_indices
]

aligned_review = review_embeddings[
    review_indices
]


print()
print(
    "Aligned text:",
    aligned_text.shape
)

print(
    "Aligned image:",
    aligned_image.shape
)

print(
    "Aligned review:",
    aligned_review.shape
)


# ============================================================
# LOAD EXISTING TEXT PROJECTION
# ============================================================

print()
print("Loading text projection...")

text_projection = np.load(
    TEXT_PROJECTION_PATH
).astype(
    np.float32
)

print(
    "Text projection:",
    text_projection.shape
)


# ============================================================
# PROJECT TEXT
# ============================================================

projected_text = (
    aligned_text
    @ text_projection
).astype(
    np.float32
)


# ============================================================
# IMAGE PROJECTION
# ============================================================

print()
print("Creating image projection...")

# Use a deterministic random projection.
# 2048 -> 256

rng = np.random.default_rng(
    42
)

image_projection = (
    rng.standard_normal(
        (
            aligned_image.shape[1],
            TARGET_DIMENSION
        )
    )
    / np.sqrt(
        TARGET_DIMENSION
    )
).astype(
    np.float32
)

np.save(
    IMAGE_PROJECTION_PATH,
    image_projection
)

projected_image = (
    aligned_image
    @ image_projection
).astype(
    np.float32
)


# ============================================================
# REVIEW PROJECTION
# ============================================================

print()
print("Creating review projection...")

# Review embeddings are also 384 dimensions.
# Reuse the same 384 -> 256 projection structure
# as the text modality.

review_projection = text_projection.copy()

np.save(
    REVIEW_PROJECTION_PATH,
    review_projection
)

projected_review = (
    aligned_review
    @ review_projection
).astype(
    np.float32
)


# ============================================================
# NORMALIZATION FUNCTION
# ============================================================

def normalize_rows(
    embeddings
):

    norms = np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True
    )

    norms[norms == 0] = 1.0

    return (
        embeddings / norms
    ).astype(
        np.float32
    )


# ============================================================
# NORMALIZE EACH MODALITY
# ============================================================

print()
print("Normalizing modalities...")

projected_text = normalize_rows(
    projected_text
)

projected_image = normalize_rows(
    projected_image
)

projected_review = normalize_rows(
    projected_review
)


print(
    "Text projected:",
    projected_text.shape
)

print(
    "Image projected:",
    projected_image.shape
)

print(
    "Review projected:",
    projected_review.shape
)


# ============================================================
# WEIGHTED MULTIMODAL FUSION
# ============================================================

print()
print("=" * 70)
print("FUSING THREE MODALITIES")
print("=" * 70)

print()
print(
    f"Image weight : {IMAGE_WEIGHT}"
)

print(
    f"Text weight  : {TEXT_WEIGHT}"
)

print(
    f"Review weight: {REVIEW_WEIGHT}"
)


three_modal_embeddings = (
    IMAGE_WEIGHT * projected_image
    +
    TEXT_WEIGHT * projected_text
    +
    REVIEW_WEIGHT * projected_review
).astype(
    np.float32
)


# ============================================================
# NORMALIZE FINAL FUSED EMBEDDINGS
# ============================================================

three_modal_embeddings = normalize_rows(
    three_modal_embeddings
)


# ============================================================
# REPORT FUSION
# ============================================================

print()
print(
    "Final 3-modal embedding shape:",
    three_modal_embeddings.shape
)

print(
    "Expected shape:",
    (
        len(common_product_ids),
        TARGET_DIMENSION
    )
)

print(
    "First vector norm:",
    np.linalg.norm(
        three_modal_embeddings[0]
    )
)


# ============================================================
# SAVE EMBEDDINGS
# ============================================================

print()
print("Saving 3-modal embeddings...")

np.save(
    OUTPUT_EMBEDDINGS_PATH,
    three_modal_embeddings
)

pd.DataFrame(
    {
        "product_id":
        common_product_ids
    }
).to_csv(
    OUTPUT_PRODUCT_IDS_PATH,
    index=False
)


# ============================================================
# BUILD FAISS INDEX
# ============================================================

print()
print("=" * 70)
print("BUILDING 3-MODAL FAISS INDEX")
print("=" * 70)

dimension = (
    three_modal_embeddings.shape[1]
)

index = faiss.IndexFlatIP(
    dimension
)

index.add(
    three_modal_embeddings
)

print()
print(
    "FAISS index type:",
    "IndexFlatIP"
)

print(
    "FAISS vectors:",
    index.ntotal
)

print(
    "FAISS dimension:",
    index.d
)


# ============================================================
# SAVE FAISS INDEX
# ============================================================

faiss.write_index(
    index,
    str(THREE_MODAL_INDEX_PATH)
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("3-MODAL FUSION COMPLETE")
print("=" * 70)

print()

print(
    "Products:",
    len(common_product_ids)
)

print(
    "Embedding dimension:",
    dimension
)

print(
    "Image weight:",
    IMAGE_WEIGHT
)

print(
    "Text weight:",
    TEXT_WEIGHT
)

print(
    "Review weight:",
    REVIEW_WEIGHT
)

print()

print(
    "Saved embedding:"
)

print(
    OUTPUT_EMBEDDINGS_PATH
)

print()

print(
    "Saved product IDs:"
)

print(
    OUTPUT_PRODUCT_IDS_PATH
)

print()

print(
    "Saved image projection:"
)

print(
    IMAGE_PROJECTION_PATH
)

print()

print(
    "Saved review projection:"
)

print(
    REVIEW_PROJECTION_PATH
)

print()

print(
    "Saved FAISS index:"
)

print(
    THREE_MODAL_INDEX_PATH
)

print()
print("=" * 70)
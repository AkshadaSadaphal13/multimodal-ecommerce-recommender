from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.preprocessing import normalize


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)


# ============================================================
# INPUT FILES
# ============================================================

TEXT_PATH = (
    EMBEDDING_DIR
    / "aligned_text_embeddings.npy"
)

IMAGE_PATH = (
    EMBEDDING_DIR
    / "aligned_image_embeddings.npy"
)

PRODUCT_IDS_PATH = (
    EMBEDDING_DIR
    / "aligned_product_ids.csv"
)


# ============================================================
# OUTPUT FILES
# ============================================================

FUSED_PATH = (
    EMBEDDING_DIR
    / "multimodal_embeddings.npy"
)

FUSED_IDS_PATH = (
    EMBEDDING_DIR
    / "multimodal_product_ids.csv"
)


# ============================================================
# SETTINGS
# ============================================================

TEXT_WEIGHT = 0.5

IMAGE_WEIGHT = 0.5

TARGET_DIMENSION = 256


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("MULTIMODAL EMBEDDING FUSION")
print("=" * 70)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

print()
print("Loading text embeddings...")

text_embeddings = np.load(
    TEXT_PATH
).astype(np.float32)

print(
    "Text shape:",
    text_embeddings.shape
)


print()
print("Loading image embeddings...")

image_embeddings = np.load(
    IMAGE_PATH
).astype(np.float32)

print(
    "Image shape:",
    image_embeddings.shape
)


# ============================================================
# VALIDATE
# ============================================================

if len(text_embeddings) != len(
    image_embeddings
):

    raise ValueError(
        "Text and image embedding counts "
        "do not match."
    )


# ============================================================
# NORMALIZE INPUT EMBEDDINGS
# ============================================================

print()
print("Normalizing embeddings...")

text_embeddings = normalize(
    text_embeddings,
    norm="l2"
).astype(np.float32)

image_embeddings = normalize(
    image_embeddings,
    norm="l2"
).astype(np.float32)


# ============================================================
# RANDOM PROJECTION
# ============================================================

print()
print(
    "Projecting both modalities "
    f"to {TARGET_DIMENSION} dimensions..."
)


# ------------------------------------------------------------
# Reproducible random generator
# ------------------------------------------------------------

rng = np.random.default_rng(
    seed=42
)


# ------------------------------------------------------------
# Text projection
# ------------------------------------------------------------

text_projection = (
    rng.standard_normal(
        (
            text_embeddings.shape[1],
            TARGET_DIMENSION
        )
    )
    / np.sqrt(
        text_embeddings.shape[1]
    )
).astype(np.float32)


# ------------------------------------------------------------
# Image projection
# ------------------------------------------------------------

image_projection = (
    rng.standard_normal(
        (
            image_embeddings.shape[1],
            TARGET_DIMENSION
        )
    )
    / np.sqrt(
        image_embeddings.shape[1]
    )
).astype(np.float32)


# ------------------------------------------------------------
# Apply projections
# ------------------------------------------------------------

text_projected = (
    text_embeddings
    @ text_projection
)

image_projected = (
    image_embeddings
    @ image_projection
)


print(
    "Projected text shape:",
    text_projected.shape
)

print(
    "Projected image shape:",
    image_projected.shape
)


# ============================================================
# NORMALIZE PROJECTED FEATURES
# ============================================================

print()
print(
    "Normalizing projected features..."
)


text_projected = normalize(
    text_projected,
    norm="l2"
).astype(np.float32)


image_projected = normalize(
    image_projected,
    norm="l2"
).astype(np.float32)


# ============================================================
# WEIGHTED FUSION
# ============================================================

print()
print(
    "Applying weighted fusion..."
)

print(
    f"Text weight: {TEXT_WEIGHT}"
)

print(
    f"Image weight: {IMAGE_WEIGHT}"
)


multimodal_embeddings = (
    TEXT_WEIGHT
    * text_projected
    +
    IMAGE_WEIGHT
    * image_projected
)


# ============================================================
# FINAL NORMALIZATION
# ============================================================

print()
print(
    "Applying final L2 normalization..."
)

multimodal_embeddings = normalize(
    multimodal_embeddings,
    norm="l2"
).astype(np.float32)


# ============================================================
# SAVE
# ============================================================

print()
print(
    "Saving multimodal embeddings..."
)


np.save(
    FUSED_PATH,
    multimodal_embeddings
)


# ============================================================
# SAVE PRODUCT IDS
# ============================================================

product_ids = pd.read_csv(
    PRODUCT_IDS_PATH
)

product_ids.to_csv(
    FUSED_IDS_PATH,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("MULTIMODAL FUSION COMPLETE")
print("=" * 70)

print()

print(
    "Text embeddings:",
    text_embeddings.shape
)

print(
    "Image embeddings:",
    image_embeddings.shape
)

print(
    "Final multimodal embeddings:",
    multimodal_embeddings.shape
)

print()

print(
    "Text weight:",
    TEXT_WEIGHT
)

print(
    "Image weight:",
    IMAGE_WEIGHT
)

print()

print(
    "Embedding dtype:",
    multimodal_embeddings.dtype
)

print()

print(
    "Embedding norm of first product:",
    np.linalg.norm(
        multimodal_embeddings[0]
    )
)

print()

print(
    "Saved:"
)

print(
    FUSED_PATH
)

print(
    FUSED_IDS_PATH
)

print()

print("=" * 70)
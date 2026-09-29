from pathlib import Path
import numpy as np


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

EMBEDDING_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

TEXT_DIM = 384
IMAGE_DIM = 2048
TARGET_DIM = 256

SEED = 42


# ============================================================
# RECREATE SAME RANDOM PROJECTIONS
# ============================================================

print()
print("=" * 70)
print("SAVING PROJECTION MATRICES")
print("=" * 70)

print()

print("Seed:", SEED)

rng = np.random.default_rng(
    seed=SEED
)


# Text projection
text_projection = (
    rng.standard_normal(
        (
            TEXT_DIM,
            TARGET_DIM
        )
    )
    / np.sqrt(TEXT_DIM)
).astype(np.float32)


# Image projection
image_projection = (
    rng.standard_normal(
        (
            IMAGE_DIM,
            TARGET_DIM
        )
    )
    / np.sqrt(IMAGE_DIM)
).astype(np.float32)


# ============================================================
# SAVE
# ============================================================

text_path = (
    EMBEDDING_DIR
    / "text_projection.npy"
)

image_path = (
    EMBEDDING_DIR
    / "image_projection.npy"
)


np.save(
    text_path,
    text_projection
)

np.save(
    image_path,
    image_projection
)


# ============================================================
# REPORT
# ============================================================

print()

print(
    "Text projection:",
    text_projection.shape
)

print(
    "Image projection:",
    image_projection.shape
)

print()

print(
    "Saved:"
)

print(
    text_path
)

print(
    image_path
)

print()

print("=" * 70)
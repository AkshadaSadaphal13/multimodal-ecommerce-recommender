from pathlib import Path

import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multimodal.csv"
)

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

EMBEDDING_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_EMBEDDINGS = (
    EMBEDDING_DIR
    / "text_embeddings.npy"
)

OUTPUT_PRODUCT_IDS = (
    EMBEDDING_DIR
    / "text_product_ids.csv"
)


# ============================================================
# MODEL
# ============================================================

MODEL_NAME = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# LOAD DATA
# ============================================================

print()
print("=" * 70)
print("TEXT EMBEDDING GENERATION")
print("=" * 70)

print()
print("Loading dataset...")

df = pd.read_csv(
    INPUT_PATH
)

print(
    f"Products loaded: {len(df)}"
)


# ============================================================
# CREATE TEXT
# ============================================================

print()
print("Preparing product text...")

df["combined_text"] = (
    df["title"]
    .fillna("")
    .astype(str)

    + " "

    + df["features"]
    .fillna("")
    .astype(str)

    + " "

    + df["description"]
    .fillna("")
    .astype(str)
)


# Clean whitespace
df["combined_text"] = (
    df["combined_text"]
    .str.replace(
        r"\s+",
        " ",
        regex=True
    )
    .str.strip()
)


# ============================================================
# LOAD SBERT
# ============================================================

print()
print("Loading SBERT model:")

print(MODEL_NAME)

model = SentenceTransformer(
    MODEL_NAME
)


# ============================================================
# GENERATE EMBEDDINGS
# ============================================================

print()
print("Generating text embeddings...")
print("This may take some time.")

texts = (
    df["combined_text"]
    .tolist()
)

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True,
    normalize_embeddings=True
)


# ============================================================
# SAVE EMBEDDINGS
# ============================================================

print()
print("Saving embeddings...")

np.save(
    OUTPUT_EMBEDDINGS,
    embeddings.astype(
        np.float32
    )
)


# ============================================================
# SAVE PRODUCT ID MAPPING
# ============================================================

product_ids = pd.DataFrame({
    "product_id": df["product_id"]
})

product_ids.to_csv(
    OUTPUT_PRODUCT_IDS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# VERIFY
# ============================================================

print()
print("=" * 70)
print("TEXT EMBEDDINGS COMPLETE")
print("=" * 70)

print()

print(
    "Embedding shape:"
)

print(
    embeddings.shape
)

print()

print(
    "Expected:"
)

print(
    f"({len(df)}, 384)"
)

print()

print(
    "Embedding dtype:"
)

print(
    embeddings.dtype
)

print()

print(
    "Saved embeddings:"
)

print(
    OUTPUT_EMBEDDINGS
)

print()

print(
    "Saved product IDs:"
)

print(
    OUTPUT_PRODUCT_IDS
)

print()

print(
    "First embedding:"
)

print(
    embeddings[0][:10]
)

print()
print("=" * 70)
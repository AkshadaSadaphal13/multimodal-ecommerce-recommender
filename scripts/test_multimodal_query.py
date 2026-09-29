from pathlib import Path

import faiss
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

INDEX_PATH = (
    PROJECT_ROOT
    / "index"
    / "multimodal_product_index.faiss"
)

PRODUCT_IDS_PATH = (
    EMBEDDING_DIR
    / "multimodal_product_ids.csv"
)

PRODUCTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_aligned.csv"
)

TEXT_PROJECTION_PATH = (
    EMBEDDING_DIR
    / "text_projection.npy"
)


# ============================================================
# SETTINGS
# ============================================================

QUERY = "beauty cleanser"

TOP_K = 10


# ============================================================
# LOAD MODEL
# ============================================================

print()
print("=" * 70)
print("MULTIMODAL TEXT QUERY TEST")
print("=" * 70)

print()

print(
    "Query:",
    QUERY
)

print()

print(
    "Loading SBERT..."
)

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# CREATE QUERY EMBEDDING
# ============================================================

print()

print(
    "Creating text query embedding..."
)

query_text_embedding = model.encode(
    [QUERY],
    convert_to_numpy=True,
    normalize_embeddings=True
).astype(np.float32)


print(
    "SBERT query shape:",
    query_text_embedding.shape
)


# ============================================================
# LOAD TEXT PROJECTION
# ============================================================

print()

print(
    "Loading text projection..."
)

text_projection = np.load(
    TEXT_PROJECTION_PATH
).astype(np.float32)


print(
    "Projection shape:",
    text_projection.shape
)


# ============================================================
# PROJECT QUERY TO 256-D
# ============================================================

query_vector = (
    query_text_embedding
    @ text_projection
)


# Normalize
query_norm = np.linalg.norm(
    query_vector,
    axis=1,
    keepdims=True
)

query_vector = (
    query_vector
    / np.maximum(
        query_norm,
        1e-12
    )
).astype(np.float32)


print()

print(
    "Projected query shape:",
    query_vector.shape
)


# ============================================================
# LOAD FAISS
# ============================================================

print()

print(
    "Loading multimodal FAISS..."
)

index = faiss.read_index(
    str(INDEX_PATH)
)

print(
    "FAISS vectors:",
    index.ntotal
)


# ============================================================
# SEARCH
# ============================================================

print()

print(
    "Searching..."
)

scores, indices = index.search(
    query_vector,
    TOP_K
)


# ============================================================
# LOAD PRODUCT DATA
# ============================================================

product_ids = pd.read_csv(
    PRODUCT_IDS_PATH
)

products = pd.read_csv(
    PRODUCTS_PATH
)

products["product_id"] = (
    products["product_id"]
    .astype(str)
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print()

print("=" * 70)
print("TOP RECOMMENDATIONS")
print("=" * 70)

print()

for rank, (
    score,
    index_position
) in enumerate(
    zip(
        scores[0],
        indices[0]
    ),
    start=1
):

    if index_position < 0:
        continue

    product_id = str(
        product_ids.iloc[
            index_position
        ]["product_id"]
    )

    matches = products[
        products["product_id"]
        == product_id
    ]

    if len(matches) == 0:
        continue

    row = matches.iloc[0]

    print(
        f"{rank}. "
        f"{row.get('title', '')}"
    )

    print(
        f"   Product ID: {product_id}"
    )

    print(
        f"   Category: "
        f"{row.get('main_category', '')}"
    )

    print(
        f"   Similarity: "
        f"{score:.4f}"
    )

    print()
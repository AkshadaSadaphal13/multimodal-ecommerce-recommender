from pathlib import Path

import faiss
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

INDEX_DIR = (
    PROJECT_ROOT
    / "index"
)

INDEX_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# INPUTS
# ============================================================

EMBEDDINGS_PATH = (
    EMBEDDING_DIR
    / "multimodal_embeddings.npy"
)

PRODUCT_IDS_PATH = (
    EMBEDDING_DIR
    / "multimodal_product_ids.csv"
)


# ============================================================
# OUTPUT
# ============================================================

INDEX_PATH = (
    INDEX_DIR
    / "multimodal_product_index.faiss"
)


# ============================================================
# HEADER
# ============================================================

print()
print("=" * 70)
print("BUILDING MULTIMODAL FAISS INDEX")
print("=" * 70)


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

print()
print("Loading multimodal embeddings...")

embeddings = np.load(
    EMBEDDINGS_PATH
).astype(np.float32)

print(
    "Embedding shape:",
    embeddings.shape
)


# ============================================================
# LOAD PRODUCT IDS
# ============================================================

print()
print("Loading product IDs...")

product_ids = pd.read_csv(
    PRODUCT_IDS_PATH
)

print(
    "Product IDs:",
    len(product_ids)
)


# ============================================================
# VALIDATION
# ============================================================

if len(embeddings) != len(product_ids):

    raise ValueError(
        "Embedding count does not match "
        "product ID count."
    )


if embeddings.ndim != 2:

    raise ValueError(
        "Embeddings must be a 2D matrix."
    )


# ============================================================
# CHECK NORMALIZATION
# ============================================================

print()
print("Checking embedding normalization...")

norms = np.linalg.norm(
    embeddings,
    axis=1
)

print(
    "Minimum norm:",
    norms.min()
)

print(
    "Maximum norm:",
    norms.max()
)

print(
    "Average norm:",
    norms.mean()
)


# ============================================================
# BUILD INDEX
# ============================================================

dimension = embeddings.shape[1]

print()
print(
    f"Creating FAISS IndexFlatIP "
    f"with dimension {dimension}..."
)


# Inner Product
#
# Because embeddings are L2 normalized:
#
# Inner Product = Cosine Similarity

index = faiss.IndexFlatIP(
    dimension
)


# ============================================================
# ADD EMBEDDINGS
# ============================================================

print()
print("Adding embeddings to FAISS...")

index.add(
    embeddings
)

print(
    "Vectors in index:",
    index.ntotal
)


# ============================================================
# SAVE INDEX
# ============================================================

print()
print("Saving FAISS index...")

faiss.write_index(
    index,
    str(INDEX_PATH)
)


# ============================================================
# TEST SEARCH
# ============================================================

print()
print("Testing FAISS search...")

# Search using first product
query = embeddings[
    0:1
]

k = 5

scores, indices = index.search(
    query,
    k
)


print()
print("Top 5 results for first product:")

for rank, (
    score,
    idx
) in enumerate(
    zip(
        scores[0],
        indices[0]
    ),
    start=1
):

    product_id = (
        product_ids.iloc[idx][
            "product_id"
        ]
    )

    print(
        f"{rank}. "
        f"{product_id} "
        f"| similarity = "
        f"{score:.4f}"
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("MULTIMODAL FAISS INDEX COMPLETE")
print("=" * 70)

print()

print(
    "Dimension:",
    dimension
)

print(
    "Vectors:",
    index.ntotal
)

print()

print(
    "Index type:",
    type(index).__name__
)

print()

print(
    "Saved to:"
)

print(
    INDEX_PATH
)

print()

print("=" * 70)
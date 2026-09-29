"""FAISS index utilities for vector retrieval."""

from __future__ import annotations

import os

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover - optional dependency
    faiss = None


def build_faiss_index(embeddings, index_path: str):
    """Create a FAISS index or fallback to a NumPy file when faiss is unavailable."""
    array = np.asarray(embeddings, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)

    if faiss is not None:
        index = faiss.IndexFlatL2(array.shape[1])
        index.add(array)
        faiss.write_index(index, index_path)
        return index_path

    os.makedirs(os.path.dirname(index_path) or '.', exist_ok=True)
    np.save(index_path, array)
    return index_path


def load_faiss_index(index_path: str):
    if faiss is not None and os.path.exists(index_path):
        return faiss.read_index(index_path)
    return None

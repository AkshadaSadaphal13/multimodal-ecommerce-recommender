"""Cosine-similarity utilities for recommendation retrieval."""

from __future__ import annotations

import numpy as np


def cosine_similarity(query_vector, candidate_vectors):
    query = np.asarray(query_vector, dtype=np.float32).reshape(1, -1)
    candidates = np.asarray(candidate_vectors, dtype=np.float32)

    if candidates.ndim == 1:
        candidates = candidates.reshape(1, -1)

    query_norm = np.linalg.norm(query, axis=1, keepdims=True)
    candidate_norms = np.linalg.norm(candidates, axis=1, keepdims=True)
    denominator = query_norm * candidate_norms.T
    numerator = query @ candidates.T
    return (numerator / np.clip(denominator, 1e-12, None)).reshape(-1)

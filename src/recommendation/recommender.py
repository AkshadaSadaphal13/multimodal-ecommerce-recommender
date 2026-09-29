"""Recommendation engine using cosine similarity and ranking."""

from __future__ import annotations

import numpy as np

from src.retrieval.similarity import cosine_similarity
from src.ranking.ranker import rank_products


def recommend(products, embeddings, query_embedding, top_k: int = 10):
    """Return top-k recommended products with similarity scores."""
    if not products:
        return []

    candidates = np.asarray(embeddings, dtype=np.float32)
    query = np.asarray(query_embedding, dtype=np.float32)
    scores = cosine_similarity(query, candidates)
    ranked_indices = rank_products(scores, top_k=top_k)

    results = []
    for rank_position, idx in enumerate(ranked_indices):
        results.append({
            'rank': rank_position + 1,
            'index': int(idx),
            'score': float(scores[idx]),
            'product': products[idx],
        })
    return results

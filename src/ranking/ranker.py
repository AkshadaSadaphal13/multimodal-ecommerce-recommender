"""Ranking mechanism for Top-K recommendation output."""

from __future__ import annotations

import numpy as np


def rank_products(scores, top_k: int = 10):
    score_array = np.asarray(scores, dtype=np.float32)
    ranked_indices = np.argsort(score_array)[::-1]
    if top_k is None:
        top_k = len(ranked_indices)
    return ranked_indices[:top_k].tolist()

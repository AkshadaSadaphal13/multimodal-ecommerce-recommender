"""Multimodal fusion utilities for image, text, and review embeddings."""

from __future__ import annotations

import numpy as np


def _normalize_matrix(matrix):
    array = np.asarray(matrix, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norm = np.linalg.norm(array, axis=1, keepdims=True)
    norm = np.where(norm == 0, 1.0, norm)
    return array / norm


def fuse_features(image_features, text_features, review_features=None, alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2):
    """Weighted late fusion:
        F = alpha * I + beta * D + gamma * R
    """
    image = _normalize_matrix(image_features)
    text = _normalize_matrix(text_features)

    if review_features is None:
        return (alpha * image + beta * text).astype(np.float32)

    review = _normalize_matrix(review_features)
    fused = alpha * image + beta * text + gamma * review
    return fused.astype(np.float32)


def fuse_product_embeddings(image_embeddings, text_embeddings, review_embeddings=None, alpha: float = 0.4, beta: float = 0.4, gamma: float = 0.2):
    if review_embeddings is None:
        return fuse_features(image_embeddings, text_embeddings, alpha=alpha, beta=beta, gamma=gamma)
    return fuse_features(image_embeddings, text_embeddings, review_embeddings, alpha=alpha, beta=beta, gamma=gamma)

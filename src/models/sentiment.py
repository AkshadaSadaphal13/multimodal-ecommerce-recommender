"""Sentiment analysis layer for customer reviews."""

from __future__ import annotations

from typing import Iterable, List

from transformers import pipeline


class SentimentAnalyzer:
    """Estimate sentiment polarity for product reviews."""

    def __init__(self, model_name: str = 'distilbert-base-uncased-finetuned-sentiment'):
        self.model_name = model_name
        self.model = pipeline('sentiment-analysis', model=model_name)

    def predict(self, texts: Iterable[str]) -> List[dict]:
        values = list(texts)
        if not values:
            return []
        return self.model(values)

    def analyze(self, texts: Iterable[str]) -> List[dict]:
        return self.predict(texts)

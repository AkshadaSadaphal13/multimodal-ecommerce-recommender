"""Text encoder module built around a transformer backbone."""

from __future__ import annotations

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer


class TextEncoder:
    """Generate semantic embeddings from product descriptions, queries, and reviews."""

    def __init__(self, model_name: str = 'distilbert-base-uncased', device: str = 'cpu'):
        self.model_name = model_name
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(device)
        self.model.eval()

    def _mean_pool(self, hidden_states, attention_mask):
        mask = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
        pooled = torch.sum(hidden_states * mask, dim=1)
        mask_sum = torch.clamp(mask.sum(dim=1), min=1e-9)
        return pooled / mask_sum

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        inputs = self.tokenizer(list(texts), return_tensors='pt', padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            embeddings = self._mean_pool(outputs.last_hidden_state, inputs['attention_mask'])
        return embeddings.cpu().numpy().astype(np.float32)

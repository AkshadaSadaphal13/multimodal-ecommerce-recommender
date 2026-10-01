from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

import faiss
import numpy as np
import pandas as pd
from PIL import Image
from sentence_transformers import SentenceTransformer
import torch
from torchvision import models


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RetrievalService:
    """Content-aware retrieval for text, image and multimodal shopping search.

    Text queries use a text-only FAISS index, image queries use an image-only
    index, and image+text queries use the existing three-modal index.
    """

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    TOP_CANDIDATE_MULTIPLIER = 8
    MIN_CANDIDATES = 80

    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for",
        "from", "in", "into", "is", "it", "me", "my", "of", "on",
        "or", "please", "show", "some", "the", "to", "under", "with",
        "without", "for", "looking", "want", "find", "get", "give",
        "best", "good", "new", "product", "products", "item", "items",
    }

    def __init__(self):
        self.index_dir = PROJECT_ROOT / "index"
        self.embedding_dir = PROJECT_ROOT / "data" / "embeddings"
        self.products_path = PROJECT_ROOT / "data" / "processed" / "products_aligned.csv"
        self.reviews_path = PROJECT_ROOT / "data" / "processed" / "reviews_multicategory_sentiment.csv"

        self.text_index = self._load_index("text_product_index.faiss")
        self.image_index = self._load_index("image_product_index.faiss")
        self.multimodal_index = self._load_index("three_modal_product_index.faiss")

        self.text_product_ids = self._load_ids("text_product_ids.csv", fallback="aligned_product_ids.csv")
        self.image_product_ids = self._load_ids("image_product_ids.csv", fallback="aligned_product_ids.csv")
        self.multimodal_product_ids = self._load_ids("three_modal_product_ids.csv")

        self.products = pd.read_csv(self.products_path)
        self.products["product_id"] = self.products["product_id"].astype(str).str.strip()
        self.product_lookup = self.products.set_index("product_id", drop=False).to_dict(orient="index")

        self.text_projection = np.load(self.embedding_dir / "text_projection.npy").astype(np.float32)
        self.image_projection = np.load(self.embedding_dir / "image_projection.npy").astype(np.float32)

        self.model = SentenceTransformer(self.MODEL_NAME)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        weights = models.ResNet50_Weights.DEFAULT
        backbone = models.resnet50(weights=weights)
        backbone.fc = torch.nn.Identity()
        self.image_model = backbone.to(self.device).eval()
        self.image_transform = weights.transforms()

        self.review_stats = self._load_review_stats()

        print("=" * 70)
        print("MULTIMODAL RETRIEVAL SYSTEM READY")
        print("Text vectors:", self.text_index.ntotal)
        print("Image vectors:", self.image_index.ntotal)
        print("Multimodal vectors:", self.multimodal_index.ntotal)
        print("Text projection:", self.text_projection.shape)
        print("Image projection:", self.image_projection.shape)
        print("Image device:", self.device)
        print("=" * 70)

    @staticmethod
    def _load_index(filename: str):
        path = PROJECT_ROOT / "index" / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Missing FAISS index: {path}\n"
                "Run scripts/build_modality_indexes.py first."
            )
        return faiss.read_index(str(path))

    def _load_ids(self, filename: str, fallback: str | None = None) -> pd.DataFrame:
        path = self.embedding_dir / filename
        if not path.exists() and fallback:
            path = self.embedding_dir / fallback
        if not path.exists():
            raise FileNotFoundError(f"Missing product-ID mapping: {path}")
        df = pd.read_csv(path)
        if "product_id" not in df.columns:
            raise ValueError(f"{path} must contain a product_id column")
        df["product_id"] = df["product_id"].astype(str).str.strip()
        return df[["product_id"]].reset_index(drop=True)

    def _load_review_stats(self) -> dict[str, dict[str, Any]]:
        if not self.reviews_path.exists():
            return {}
        reviews = pd.read_csv(self.reviews_path)
        required = {"product_id", "rating", "sentiment"}
        if not required.issubset(reviews.columns):
            return {}
        reviews["product_id"] = reviews["product_id"].astype(str).str.strip()
        reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
        reviews["sentiment"] = reviews["sentiment"].astype(str).str.upper()
        stats: dict[str, dict[str, Any]] = {}
        for product_id, group in reviews.groupby("product_id", sort=False):
            ratings = group["rating"].dropna()
            total = len(group)
            positive = int((group["sentiment"] == "POSITIVE").sum())
            negative = int((group["sentiment"] == "NEGATIVE").sum())
            positive_pct = positive / total * 100 if total else 0.0
            negative_pct = negative / total * 100 if total else 0.0
            overall = "Positive" if positive_pct >= 60 else "Negative" if negative_pct >= 60 else "Mixed"
            stats[str(product_id)] = {
                "review_count": int(total),
                "average_review_rating": self.safe_float(ratings.mean() if len(ratings) else None),
                "positive_review_percentage": round(positive_pct, 2),
                "negative_review_percentage": round(negative_pct, 2),
                "overall_sentiment": overall,
            }
        return stats

    @staticmethod
    def safe_float(value):
        try:
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def safe_string(value) -> str:
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        return str(value)

    @classmethod
    def _valid_url(cls, value: Any) -> bool:
        return isinstance(value, str) and value.strip().lower().startswith(("http://", "https://"))

    @classmethod
    def _iter_image_values(cls, value: Any) -> Iterable[str]:
        """Recursively extract every usable image URL from Amazon metadata.

        The metadata can contain a direct URL, a JSON/Python string, a list of
        image dictionaries, or nested dictionaries/lists. We keep ALL candidates
        so the frontend can fall back when one Amazon image URL is dead.
        """
        if value is None:
            return

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return

            if cls._valid_url(text):
                yield text.strip(" '\"[]{}()")
                return

            # CSV stores lists/dicts as strings. Try both common formats.
            for parser in (json.loads, ast.literal_eval):
                try:
                    parsed = parser(text)
                    yield from cls._iter_image_values(parsed)
                    return
                except Exception:
                    pass

            # Last-resort extraction for malformed serialized metadata.
            for url in re.findall(r"https?://[^\s\"'\\\]\[{},]+", text):
                if cls._valid_url(url):
                    yield url.strip(" ,'\"")
            return

        if isinstance(value, dict):
            # Prefer Amazon's higher-resolution variants first, but inspect every
            # value so nested/list representations are not silently discarded.
            preferred = ("hi_res", "large", "medium", "thumb", "url")
            seen_keys = set()
            for key in preferred:
                if key in value:
                    seen_keys.add(key)
                    yield from cls._iter_image_values(value.get(key))
            for key, item in value.items():
                if key not in seen_keys:
                    yield from cls._iter_image_values(item)
            return

        if isinstance(value, (list, tuple, set)):
            for item in value:
                yield from cls._iter_image_values(item)

    @classmethod
    def extract_image_urls(cls, images: Any) -> list[str]:
        seen = set()
        result = []
        for url in cls._iter_image_values(images):
            if url and url not in seen:
                seen.add(url)
                result.append(url)
        return result

    @classmethod
    def extract_image_url(cls, images: Any) -> str:
        urls = cls.extract_image_urls(images)
        return urls[0] if urls else ""

    @staticmethod
    def _normalise_token(token: str) -> str:
        token = re.sub(r"[^a-z0-9]+", "", token.lower())
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        return token

    def _query_tokens(self, query: str) -> list[str]:
        raw = re.findall(r"[a-zA-Z0-9]+", query.lower())
        tokens = []
        for token in raw:
            normalized = self._normalise_token(token)
            if normalized and normalized not in self.STOP_WORDS and len(normalized) > 1:
                tokens.append(normalized)
        return list(dict.fromkeys(tokens))

    def _product_text(self, product: dict[str, Any]) -> str:
        values = []
        for key in (
            "title", "features", "description", "categories",
            "category", "main_category", "store", "brand", "details"
        ):
            values.append(self.safe_string(product.get(key)))
        return " ".join(values).lower()

    def _lexical_score(self, query: str, product: dict[str, Any]) -> float:
        tokens = self._query_tokens(query)
        if not tokens:
            return 0.0
        title = self.safe_string(product.get("title")).lower()
        searchable = self._product_text(product)
        matched = 0
        for token in tokens:
            if token in searchable:
                matched += 1
        coverage = matched / len(tokens)
        title_norm = " ".join(self._normalise_token(x) for x in re.findall(r"[a-zA-Z0-9]+", title))
        title_hits = sum(1 for token in tokens if token in title_norm)
        title_score = title_hits / len(tokens)
        phrase_score = 1.0 if query.lower().strip() in title else 0.0
        return min(1.0, 0.55 * coverage + 0.40 * title_score + 0.05 * phrase_score)

    def _category_score(self, query: str, product: dict[str, Any]) -> float:
        q = set(self._query_tokens(query))
        category = self._normalise_token(self.safe_string(product.get("main_category") or product.get("category")))
        text = self._product_text(product)
        # Generic category alignment; no hard-coded product category list.
        if not q or not category:
            return 0.0
        hits = sum(1 for token in q if token in category or token in text)
        return min(1.0, hits / len(q))

    def _query_embedding(self, query: str) -> np.ndarray:
        emb = self.model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True
        ).astype(np.float32)
        emb = (emb @ self.text_projection).astype(np.float32)
        faiss.normalize_L2(emb)
        return emb

    def _image_embedding(self, image_input: bytes | Image.Image) -> np.ndarray:
        if isinstance(image_input, Image.Image):
            image = image_input.convert("RGB")
        else:
            from io import BytesIO
            image = Image.open(BytesIO(image_input)).convert("RGB")
        tensor = self.image_transform(image).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            vector = self.image_model(tensor).detach().cpu().numpy().astype(np.float32)
        vector = vector @ self.image_projection
        faiss.normalize_L2(vector)
        return vector.astype(np.float32)

    def _filter_product(self, product: dict[str, Any], category, min_rating, max_price) -> bool:
        if category:
            wanted = str(category).strip().lower()
            available = " ".join([
                self.safe_string(product.get("main_category")),
                self.safe_string(product.get("category")),
                self.safe_string(product.get("categories")),
            ]).lower()
            if wanted not in available:
                return False
        if min_rating is not None:
            rating = self.safe_float(product.get("average_rating", product.get("rating")))
            if rating is None or rating < float(min_rating):
                return False
        if max_price is not None:
            price = self.safe_float(product.get("price"))
            if price is None or price > float(max_price):
                return False
        return True

    def _make_result(self, product_id: str, raw_score: float, query: str = "", mode: str = "text"):
        product = self.product_lookup.get(str(product_id).strip())
        if not product:
            return None
        review = self.review_stats.get(str(product_id).strip(), {})
        image_sources = [product.get("images"), product.get("image_urls"), product.get("image_url")]
        image_urls = []
        seen_image_urls = set()
        for source in image_sources:
            for url in self.extract_image_urls(source):
                if url not in seen_image_urls:
                    seen_image_urls.add(url)
                    image_urls.append(url)
        category = product.get("main_category") or product.get("category") or product.get("categories")
        rating = self.safe_float(product.get("average_rating", product.get("rating")))
        price = self.safe_float(product.get("price"))
        semantic = max(0.0, min(1.0, float(raw_score)))
        lexical = self._lexical_score(query, product) if query else 0.0
        category_match = self._category_score(query, product) if query else 0.0
        if mode == "text":
            final_score = 0.72 * semantic + 0.23 * lexical + 0.05 * category_match
        else:
            final_score = semantic
        final_score = max(0.0, min(1.0, final_score))
        sentiment = review.get("overall_sentiment", "Mixed")
        if mode == "image":
            reason = "Strong visual similarity to your uploaded image."
        elif lexical >= 0.65:
            reason = "Strong match with the words and product details in your search."
        elif category_match >= 0.65:
            reason = "Matches the requested product category with good semantic similarity."
        else:
            reason = "Semantically similar product based on its title, features and description."
        if sentiment == "Positive":
            reason += " Customer feedback is predominantly positive."
        return {
            "product_id": str(product_id),
            "title": self.safe_string(product.get("title")),
            "brand": self.safe_string(product.get("store") or product.get("brand")),
            "category": self.safe_string(category),
            "main_category": self.safe_string(product.get("main_category")),
            "price": price,
            "rating": rating,
            "rating_number": self.safe_float(product.get("rating_number")),
            "similarity": round(final_score, 6),
            "semantic_similarity": round(semantic, 6),
            "lexical_match": round(lexical, 6),
            "category_match": round(category_match, 6),
            "image_url": image_urls[0] if image_urls else "",
            "image_urls": image_urls,
            "images": image_urls,
            "review_count": int(review.get("review_count", 0)),
            "average_review_rating": review.get("average_review_rating"),
            "positive_review_percentage": float(review.get("positive_review_percentage", 0.0)),
            "negative_review_percentage": float(review.get("negative_review_percentage", 0.0)),
            "overall_sentiment": sentiment,
            "reason": reason,
        }

    def _retrieve(self, index, ids_df, query_vector, top_k, category=None, min_rating=None, max_price=None, query="", mode="text"):
        total = index.ntotal
        search_k = min(total, max(self.MIN_CANDIDATES, top_k * self.TOP_CANDIDATE_MULTIPLIER))
        if category or min_rating is not None or max_price is not None:
            search_k = total
        distances, indices = index.search(query_vector, search_k)
        candidates = []
        seen = set()
        for score, row_index in zip(distances[0], indices[0]):
            if row_index < 0 or row_index >= len(ids_df):
                continue
            product_id = str(ids_df.iloc[int(row_index)]["product_id"]).strip()
            if product_id in seen:
                continue
            seen.add(product_id)
            product = self.product_lookup.get(product_id)
            if not product or not self._filter_product(product, category, min_rating, max_price):
                continue
            result = self._make_result(product_id, float(score), query=query, mode=mode)
            if result:
                candidates.append(result)
        candidates.sort(key=lambda item: item["similarity"], reverse=True)
        return candidates[:top_k]

    def search(self, query, top_k=20, category=None, min_rating=None, max_price=None):
        query = str(query or "").strip()
        if not query:
            return []
        return self._retrieve(
            self.text_index,
            self.text_product_ids,
            self._query_embedding(query),
            max(1, min(int(top_k), 40)),
            category, min_rating, max_price, query, "text"
        )

    def search_by_image(self, image_input, top_k=20, category=None, min_rating=None, max_price=None):
        return self._retrieve(
            self.image_index,
            self.image_product_ids,
            self._image_embedding(image_input),
            max(1, min(int(top_k), 40)),
            category, min_rating, max_price, "", "image"
        )

    def search_multimodal(self, query, image_input, top_k=20, category=None, min_rating=None, max_price=None, text_weight=0.5, image_weight=0.5):
        query = str(query or "").strip()
        text_weight = max(0.0, float(text_weight))
        image_weight = max(0.0, float(image_weight))
        total = text_weight + image_weight
        if total <= 0:
            text_weight = image_weight = 0.5
        else:
            text_weight /= total
            image_weight /= total
        text_vector = self._query_embedding(query) if query else None
        image_vector = self._image_embedding(image_input)
        if text_vector is None:
            fused = image_vector
        else:
            fused = text_weight * text_vector + image_weight * image_vector
            faiss.normalize_L2(fused)
        return self._retrieve(
            self.multimodal_index,
            self.multimodal_product_ids,
            fused.astype(np.float32),
            max(1, min(int(top_k), 40)),
            category, min_rating, max_price, query, "multimodal"
        )

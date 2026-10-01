from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..models.user import UserPreference
from .history_service import get_user_interactions


EVENT_WEIGHTS = {
    "view": 1.0,
    "wishlist": 3.0,
    "cart": 4.0,
    "purchase": 5.0,
}
MIN_PERSONALIZATION_PRODUCTS = 3


class PersonalizationService:
    """User vectors and recommendations over the existing three-modal FAISS index."""

    def __init__(self):
        project_root = Path(__file__).resolve().parents[3]
        embedding_path = project_root / "data" / "embeddings" / "three_modal_embeddings.npy"
        product_ids_path = project_root / "data" / "embeddings" / "three_modal_product_ids.csv"
        products_path = project_root / "data" / "processed" / "products_aligned.csv"
        index_path = project_root / "index" / "three_modal_product_index.faiss"

        for path in (embedding_path, product_ids_path, products_path, index_path):
            if not path.exists():
                raise FileNotFoundError(f"Personalization data is missing: {path}")

        self.embeddings = np.load(embedding_path).astype("float32")
        ids = pd.read_csv(product_ids_path)
        id_column = "product_id" if "product_id" in ids else ids.columns[0]
        self.product_ids = ids[id_column].astype(str).str.strip().tolist()
        if len(self.product_ids) != len(self.embeddings):
            raise ValueError("Personalization embedding and product ID rows are not aligned")
        self.product_id_to_index = {product_id: index for index, product_id in enumerate(self.product_ids)}

        self.products = pd.read_csv(products_path).fillna({})
        self.products["product_id"] = self.products["product_id"].astype(str).str.strip()
        self.product_lookup = self.products.set_index("product_id", drop=False).to_dict(orient="index")
        self.index = faiss.read_index(str(index_path))
        if self.index.ntotal != len(self.product_ids):
            raise ValueError("Personalization FAISS index and product ID rows are not aligned")

    def build_user_vector(self, db: Session, user_id: str, interactions=None):
        interactions = interactions if interactions is not None else get_user_interactions(db, user_id)
        weighted_sum = np.zeros(self.embeddings.shape[1], dtype="float32")
        total_weight = 0.0
        for interaction in interactions:
            product_id = str(interaction.product_id).strip()
            index = self.product_id_to_index.get(product_id)
            weight = EVENT_WEIGHTS.get(interaction.event_type, 0.0)
            if index is None or weight <= 0:
                continue
            weighted_sum += self.embeddings[index] * weight
            total_weight += weight
        if total_weight <= 0:
            return None
        user_vector = (weighted_sum / total_weight).reshape(1, -1).astype("float32")
        if not np.isfinite(user_vector).all() or np.linalg.norm(user_vector) == 0:
            return None
        faiss.normalize_L2(user_vector)
        return user_vector

    def get_user_preferences(self, db: Session, user_id: str):
        preferences = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == user_id)
            .all()
        )
        return {
            "categories": [item.category for item in preferences],
            "min_price": preferences[0].min_price if preferences else 0.0,
            "max_price": preferences[0].max_price if preferences else None,
        }

    def _valid_positive_interactions(self, interactions):
        return [
            event for event in interactions
            if event.event_type in EVENT_WEIGHTS
            and str(event.product_id).strip() in self.product_id_to_index
        ]

    def _profile(self, interactions):
        valid = self._valid_positive_interactions(interactions)
        weights = {}
        distinct = set()
        for event in valid:
            product_id = str(event.product_id).strip()
            distinct.add(product_id)
            product = self.product_lookup.get(product_id, {})
            category = self._safe_text(product.get("main_category")).strip()
            if category:
                weights[category] = weights.get(category, 0.0) + EVENT_WEIGHTS[event.event_type]
        top_categories = sorted(weights, key=weights.get, reverse=True)[:5]
        return {
            "interaction_count": len(valid),
            "distinct_product_count": len(distinct),
            "top_categories": top_categories,
            "minimum_products_for_personalization": MIN_PERSONALIZATION_PRODUCTS,
            "personalized": len(distinct) >= MIN_PERSONALIZATION_PRODUCTS,
        }

    @staticmethod
    def _safe_number(value, fallback=None):
        try:
            number = float(value)
            return number if np.isfinite(number) else fallback
        except (TypeError, ValueError):
            return fallback

    @staticmethod
    def _safe_text(value):
        if value is None or pd.isna(value):
            return ""
        return str(value)

    def _product_payload(self, product_id, similarity=None, personalized_score=None):
        row = self.product_lookup.get(str(product_id))
        if not row:
            return None
        result = {
            "product_id": str(product_id),
            "title": self._safe_text(row.get("title")),
            "category": self._safe_text(row.get("main_category")),
            "main_category": self._safe_text(row.get("main_category")),
            "price": self._safe_number(row.get("price")),
            "rating": self._safe_number(row.get("average_rating"), 0.0),
            "average_rating": self._safe_number(row.get("average_rating"), 0.0),
            "rating_number": self._safe_number(row.get("rating_number"), 0),
            "image_url": self._safe_text(row.get("image_url")),
            "images": self._safe_text(row.get("images")),
            "store": self._safe_text(row.get("store")),
        }
        if similarity is not None:
            result["similarity"] = float(similarity)
        if personalized_score is not None:
            result["personalized_score"] = float(personalized_score)
        return result

    def _faiss_candidates(self, query_vector, count, excluded):
        if query_vector is None or not self.product_ids:
            return []
        search_count = min(max(count * 8, 80), len(self.product_ids))
        scores, indexes = self.index.search(query_vector, search_count)
        results = []
        for score, index in zip(scores[0], indexes[0]):
            if index < 0:
                continue
            product_id = self.product_ids[index]
            if product_id in excluded:
                continue
            product = self._product_payload(product_id, similarity=score, personalized_score=score)
            if product:
                results.append(product)
            if len(results) >= count:
                break
        return results

    def _cold_start(self, preferences, top_k, query=None, category=None):
        category = (category or "").strip().casefold()
        query_terms = [word.casefold() for word in (query or "").split() if len(word) > 1]
        preferred_categories = {value.casefold() for value in preferences["categories"]}
        candidates = []

        for row in self.products.to_dict(orient="records"):
            product_category = self._safe_text(row.get("main_category"))
            if category and product_category.casefold() != category:
                continue
            if not category and preferred_categories and product_category.casefold() not in preferred_categories:
                continue
            searchable = " ".join(self._safe_text(row.get(key)) for key in ("title", "main_category", "store", "combined_text", "description")).casefold()
            matched_terms = sum(term in searchable for term in query_terms)
            if query_terms and matched_terms == 0:
                continue
            price = self._safe_number(row.get("price"))
            if price is not None and preferences["min_price"] is not None and price < preferences["min_price"]:
                continue
            if price is not None and preferences["max_price"] is not None and price > preferences["max_price"]:
                continue
            item = self._product_payload(row["product_id"])
            if item:
                # These are observed catalog ratings and review counts, not ML scores.
                item["cold_start_reason"] = "query_and_category" if query_terms or category else "popular_and_high_rated"
                candidates.append((matched_terms, item["rating_number"] or 0, item["rating"] or 0, item))

        if not candidates and query_terms:
            return self._cold_start(preferences, top_k, query=None, category=category)
        candidates.sort(key=lambda entry: (entry[0], entry[1], entry[2]), reverse=True)
        return [item for _, _, _, item in candidates[:top_k]]

    def _latest_view_recommendations(self, interactions, top_k, excluded):
        views = [
            event for event in interactions
            if event.event_type == "view"
            and str(event.product_id).strip() in self.product_id_to_index
        ]
        if not views:
            return []
        latest = max(views, key=lambda event: str(event.timestamp or ""))
        product_id = str(latest.product_id).strip()
        query_vector = self.embeddings[self.product_id_to_index[product_id]].reshape(1, -1).astype("float32").copy()
        faiss.normalize_L2(query_vector)
        return self._faiss_candidates(query_vector, top_k, excluded | {product_id})

    def get_personalized_recommendations(self, db: Session, user_id: str, top_k: int = 10, context_query=None, context_category=None):
        interactions = get_user_interactions(db, user_id)
        preferences = self.get_user_preferences(db, user_id)
        profile = self._profile(interactions)
        interacted_ids = {
            str(event.product_id).strip()
            for event in self._valid_positive_interactions(interactions)
        }
        because_viewed = self._latest_view_recommendations(interactions, min(top_k, 8), interacted_ids)

        if not profile["personalized"]:
            recommendations = self._cold_start(preferences, top_k, context_query, context_category)
            return {
                "user_id": user_id,
                "mode": "cold_start",
                "cold_start": True,
                "profile": profile,
                "recommendations": recommendations,
                "because_viewed": because_viewed,
                "based_on_interests": [],
            }

        user_vector = self.build_user_vector(db, user_id, interactions)
        candidates = self._faiss_candidates(user_vector, top_k * 2, interacted_ids)
        recommendations = candidates[:top_k]
        based_on_interests = candidates[top_k:top_k * 2]
        return {
            "user_id": user_id,
            "mode": "history_based",
            "cold_start": False,
            "profile": profile,
            "recommendations": recommendations,
            "because_viewed": because_viewed,
            "based_on_interests": based_on_interests,
        }


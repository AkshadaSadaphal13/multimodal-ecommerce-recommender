from pathlib import Path

import faiss
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.user import UserPreference
from app.services.history_service import (
    get_user_interactions,
    get_event_weight,
)


class PersonalizationService:

    def __init__(self):

        project_root = Path(__file__).resolve().parents[3]

        self.embedding_path = (
            project_root
            / "data"
            / "embeddings"
            / "three_modal_embeddings.npy"
        )

        self.product_ids_path = (
            project_root
            / "data"
            / "embeddings"
            / "three_modal_product_ids.csv"
        )

        self.products_path = (
            project_root
            / "data"
            / "processed"
            / "products_aligned.csv"
        )

        self.index_path = (
            project_root
            / "index"
            / "three_modal_product_index.faiss"
        )

        print("Loading personalization data...")

        self.embeddings = np.load(
            self.embedding_path
        ).astype("float32")

        product_ids_df = pd.read_csv(
            self.product_ids_path
        )

        self.product_ids = (
            product_ids_df.iloc[:, 0]
            .astype(str)
            .tolist()
        )

        self.product_id_to_index = {
            product_id: index
            for index, product_id in enumerate(
                self.product_ids
            )
        }

        self.products = pd.read_csv(
            self.products_path
        )

        self.products["product_id"] = (
            self.products["product_id"]
            .astype(str)
        )

        self.index = faiss.read_index(
            str(self.index_path)
        )

        print(
            "Personalization system loaded:",
            len(self.product_ids),
            "products"
        )

    # -----------------------------------------------------
    # USER VECTOR
    # -----------------------------------------------------

    def build_user_vector(
        self,
        db: Session,
        user_id: str,
    ):
        interactions = get_user_interactions(
            db,
            user_id
        )

        if not interactions:
            return None

        weighted_vectors = []
        total_weight = 0.0

        for interaction in interactions:

            product_id = str(
                interaction.product_id
            )

            if product_id not in self.product_id_to_index:
                continue

            index = self.product_id_to_index[
                product_id
            ]

            vector = self.embeddings[index]

            weight = get_event_weight(
                interaction.event_type
            )

            weighted_vectors.append(
                vector * weight
            )

            total_weight += weight

        if not weighted_vectors:
            return None

        user_vector = (
            np.sum(
                weighted_vectors,
                axis=0
            )
            / total_weight
        )

        user_vector = user_vector.reshape(
            1, -1
        ).astype("float32")

        # L2 normalization
        faiss.normalize_L2(
            user_vector
        )

        return user_vector

    # -----------------------------------------------------
    # USER PREFERENCES
    # -----------------------------------------------------

    def get_user_preferences(
        self,
        db: Session,
        user_id: str,
    ):

        preferences = (
            db.query(UserPreference)
            .filter(
                UserPreference.user_id == user_id
            )
            .all()
        )

        categories = [
            preference.category
            for preference in preferences
        ]

        min_price = (
            preferences[0].min_price
            if preferences
            else 0.0
        )

        max_price = (
            preferences[0].max_price
            if preferences
            else None
        )

        return {
            "categories": categories,
            "min_price": min_price,
            "max_price": max_price,
        }

    # -----------------------------------------------------
    # PERSONALIZED RECOMMENDATIONS
    # -----------------------------------------------------

    def get_personalized_recommendations(
        self,
        db: Session,
        user_id: str,
        top_k: int = 10,
    ):

        user_vector = self.build_user_vector(
            db,
            user_id
        )

        preferences = self.get_user_preferences(
            db,
            user_id
        )

        # -------------------------------------------------
        # COLD START
        # -------------------------------------------------

        if user_vector is None:

            return self._cold_start_recommendations(
                preferences,
                top_k
            )

        # -------------------------------------------------
        # FAISS CANDIDATES
        # -------------------------------------------------

        candidate_count = min(
            max(top_k * 5, 50),
            len(self.product_ids)
        )

        scores, indices = self.index.search(
            user_vector,
            candidate_count
        )

        candidates = []

        categories = set(
            category.lower()
            for category in preferences["categories"]
        )

        min_price = preferences["min_price"]
        max_price = preferences["max_price"]

        interacted_products = {
            str(interaction.product_id)
            for interaction in get_user_interactions(
                db,
                user_id
            )
        }

        for base_score, faiss_index in zip(
            scores[0],
            indices[0]
        ):

            if faiss_index < 0:
                continue

            product_id = self.product_ids[
                faiss_index
            ]

            # Don't recommend already interacted
            # products in the main personalized list.
            if product_id in interacted_products:
                continue

            row = self.products[
                self.products["product_id"]
                == product_id
            ]

            if row.empty:
                continue

            product = row.iloc[0]

            category = str(
                product.get(
                    "main_category",
                    ""
                )
            )

            try:
                price = float(
                    product.get(
                        "price",
                        0
                    )
                )
            except (
                ValueError,
                TypeError
            ):
                price = 0.0

            # Category score
            category_score = 0.0

            if category.lower() in categories:
                category_score = 1.0

            # Price score
            price_score = 1.0

            if min_price is not None:
                if price < min_price:
                    price_score = 0.0

            if max_price is not None:
                if price > max_price:
                    price_score = 0.0

            # User similarity
            product_vector = (
                self.embeddings[faiss_index]
                .reshape(1, -1)
                .astype("float32")
            )

            faiss.normalize_L2(
                product_vector
            )

            user_similarity = float(
                np.dot(
                    user_vector[0],
                    product_vector[0]
                )
            )

            # Final personalized score
            final_score = (
                0.50 * float(base_score)
                + 0.30 * user_similarity
                + 0.10 * category_score
                + 0.10 * price_score
            )

            candidates.append(
                {
                    "product_id": product_id,
                    "multimodal_score": float(
                        base_score
                    ),
                    "user_similarity": user_similarity,
                    "category_score": category_score,
                    "price_score": price_score,
                    "personalized_score": final_score,
                    "title": str(
                        product.get(
                            "title",
                            ""
                        )
                    ),
                    "category": category,
                    "price": price,
                    "rating": float(
                        product.get(
                            "average_rating",
                            0
                        )
                        or 0
                    ),
                }
            )

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        candidates.sort(
            key=lambda x: x[
                "personalized_score"
            ],
            reverse=True
        )

        return {
            "user_id": user_id,
            "cold_start": False,
            "recommendations": candidates[:top_k],
        }

    # -----------------------------------------------------
    # COLD START
    # -----------------------------------------------------

    def _cold_start_recommendations(
        self,
        preferences,
        top_k,
    ):

        categories = set(
            category.lower()
            for category in preferences["categories"]
        )

        min_price = preferences["min_price"]
        max_price = preferences["max_price"]

        candidates = []

        for _, product in self.products.iterrows():

            category = str(
                product.get(
                    "main_category",
                    ""
                )
            )

            if categories:
                if category.lower() not in categories:
                    continue

            try:
                price = float(
                    product.get(
                        "price",
                        0
                    )
                )
            except (
                ValueError,
                TypeError
            ):
                price = 0.0

            if min_price is not None:
                if price < min_price:
                    continue

            if max_price is not None:
                if price > max_price:
                    continue

            rating = float(
                product.get(
                    "average_rating",
                    0
                )
                or 0
            )

            rating_score = rating / 5.0

            candidates.append(
                {
                    "product_id": str(
                        product["product_id"]
                    ),
                    "multimodal_score": 0.0,
                    "user_similarity": 0.0,
                    "category_score": 1.0,
                    "price_score": 1.0,
                    "personalized_score": (
                        0.80 * rating_score
                        + 0.20
                    ),
                    "title": str(
                        product.get(
                            "title",
                            ""
                        )
                    ),
                    "category": category,
                    "price": price,
                    "rating": rating,
                }
            )

        candidates.sort(
            key=lambda x: x[
                "personalized_score"
            ],
            reverse=True
        )

        return {
            "user_id": None,
            "cold_start": True,
            "recommendations": candidates[:top_k],
        }
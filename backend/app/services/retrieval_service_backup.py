from pathlib import Path
import ast
import json
import math
import re

import faiss
import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class RetrievalService:

    def __init__(self):

        print()
        print("=" * 70)
        print("INITIALIZING MULTIMODAL RETRIEVAL SERVICE")
        print("=" * 70)

        # ====================================================
        # PATHS
        # ====================================================

        index_path = (
            PROJECT_ROOT
            / "index"
            / "multimodal_product_index.faiss"
        )

        product_ids_path = (
            PROJECT_ROOT
            / "data"
            / "embeddings"
            / "multimodal_product_ids.csv"
        )

        products_path = (
            PROJECT_ROOT
            / "data"
            / "processed"
            / "products_aligned.csv"
        )

        projection_path = (
            PROJECT_ROOT
            / "data"
            / "embeddings"
            / "text_projection.npy"
        )

        # ====================================================
        # LOAD FAISS
        # ====================================================

        print()
        print("Loading multimodal FAISS index...")

        self.index = faiss.read_index(
            str(index_path)
        )

        print(
            "FAISS vectors:",
            self.index.ntotal
        )

        print(
            "FAISS dimension:",
            self.index.d
        )

        # ====================================================
        # LOAD PRODUCT IDS
        # ====================================================

        print()
        print("Loading product IDs...")

        self.product_ids = pd.read_csv(
            product_ids_path
        )

        self.product_ids["product_id"] = (
            self.product_ids["product_id"]
            .astype(str)
        )

        print(
            "Product IDs:",
            len(self.product_ids)
        )

        # ====================================================
        # LOAD PRODUCT METADATA
        # ====================================================

        print()
        print("Loading product metadata...")

        self.products = pd.read_csv(
            products_path
        )

        self.products["product_id"] = (
            self.products["product_id"]
            .astype(str)
        )

        print(
            "Products:",
            len(self.products)
        )

        print(
            "Categories:"
        )

        print(
            self.products[
                "main_category"
            ]
            .value_counts()
            .to_dict()
        )

        # ====================================================
        # LOAD TEXT PROJECTION
        # ====================================================

        print()
        print("Loading text projection...")

        self.text_projection = (
            np.load(
                projection_path
            )
            .astype(np.float32)
        )

        print(
            "Text projection:",
            self.text_projection.shape
        )

        # ====================================================
        # LOAD SBERT
        # ====================================================

        print()
        print("Loading Sentence-BERT...")

        self.text_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        print(
            "Sentence-BERT loaded."
        )

        print()
        print("=" * 70)
        print("MULTIMODAL RETRIEVAL SERVICE READY")
        print("=" * 70)
        print()

    # ========================================================
    # IMAGE URL EXTRACTION
    # ========================================================

    def extract_image_url(
        self,
        image_data
    ):

        if image_data is None:
            return None

        try:

            if pd.isna(image_data):
                return None

        except Exception:

            pass

        # ----------------------------------------------------
        # STRING
        # ----------------------------------------------------

        if isinstance(
            image_data,
            str
        ):

            value = image_data.strip()

            if not value:
                return None

            if value.startswith(
                "http"
            ):

                return value.strip(
                    " ,'\"[]{}()"
                )

            # JSON
            try:

                parsed = json.loads(
                    value
                )

                result = (
                    self.extract_image_url(
                        parsed
                    )
                )

                if result:
                    return result

            except Exception:

                pass

            # Python representation
            try:

                parsed = ast.literal_eval(
                    value
                )

                result = (
                    self.extract_image_url(
                        parsed
                    )
                )

                if result:
                    return result

            except Exception:

                pass

            # URL fallback
            urls = re.findall(
                r"https?://[^\s\"'\\\]\[{},]+",
                value
            )

            if urls:

                return urls[0].strip(
                    " ,'\"[]{}()"
                )

            return None

        # ----------------------------------------------------
        # DICTIONARY
        # ----------------------------------------------------

        if isinstance(
            image_data,
            dict
        ):

            for key in [
                "hi_res",
                "large",
                "thumb"
            ]:

                value = image_data.get(
                    key
                )

                if value:

                    result = (
                        self.extract_image_url(
                            value
                        )
                    )

                    if result:
                        return result

            return None

        # ----------------------------------------------------
        # LIST / TUPLE
        # ----------------------------------------------------

        if isinstance(
            image_data,
            (list, tuple)
        ):

            for item in image_data:

                result = (
                    self.extract_image_url(
                        item
                    )
                )

                if result:
                    return result

            return None

        # ----------------------------------------------------
        # NUMPY / PANDAS
        # ----------------------------------------------------

        try:

            if hasattr(
                image_data,
                "tolist"
            ):

                return (
                    self.extract_image_url(
                        image_data.tolist()
                    )
                )

        except Exception:

            pass

        return None

    # ========================================================
    # QUERY → MULTIMODAL VECTOR
    # ========================================================

    def encode_text_query(
        self,
        query
    ):

        if not query:

            raise ValueError(
                "Query cannot be empty."
            )

        query = str(
            query
        ).strip()

        if not query:

            raise ValueError(
                "Query cannot be empty."
            )

        # ----------------------------------------------------
        # SBERT
        # ----------------------------------------------------

        embedding = self.text_model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(np.float32)

        # ----------------------------------------------------
        # 384 → 256
        # ----------------------------------------------------

        projected = (
            embedding
            @ self.text_projection
        )

        # ----------------------------------------------------
        # L2 NORMALIZATION
        # ----------------------------------------------------

        norm = np.linalg.norm(
            projected,
            axis=1,
            keepdims=True
        )

        projected = (
            projected
            / np.maximum(
                norm,
                1e-12
            )
        ).astype(np.float32)

        return projected

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self,
        query,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None
    ):

        # ----------------------------------------------------
        # ENCODE QUERY
        # ----------------------------------------------------

        query_vector = (
            self.encode_text_query(
                query
            )
        )

        # ----------------------------------------------------
        # HOW MANY PRODUCTS TO RETRIEVE
        # ----------------------------------------------------

        filters_active = (
            category is not None
            or min_rating is not None
            or max_price is not None
        )

        if filters_active:

            # Retrieve the complete index.
            #
            # Dataset = only 2499 products.
            #
            # This guarantees that filtering does not
            # accidentally remove relevant products before
            # we have seen all possible candidates.

            candidate_k = self.index.ntotal

        else:

            candidate_k = min(
                max(top_k, 1),
                self.index.ntotal
            )

        # ----------------------------------------------------
        # FAISS SEARCH
        # ----------------------------------------------------

        scores, indices = (
            self.index.search(
                query_vector,
                candidate_k
            )
        )

        results = []

        # ----------------------------------------------------
        # PROCESS CANDIDATES
        # ----------------------------------------------------

        for rank, idx in enumerate(
            indices[0]
        ):

            if idx < 0:
                continue

            if idx >= len(
                self.product_ids
            ):
                continue

            # ------------------------------------------------
            # PRODUCT ID
            # ------------------------------------------------

            product_id = str(
                self.product_ids.iloc[
                    idx
                ]["product_id"]
            )

            # ------------------------------------------------
            # PRODUCT METADATA
            # ------------------------------------------------

            product = self.products[
                self.products[
                    "product_id"
                ].astype(str)
                == product_id
            ]

            if len(product) == 0:
                continue

            row = product.iloc[0]

            # ------------------------------------------------
            # CATEGORY
            # ------------------------------------------------

            product_category = row.get(
                "main_category",
                ""
            )

            if pd.isna(
                product_category
            ):

                product_category = ""

            product_category = str(
                product_category
            ).strip()

            # ------------------------------------------------
            # CATEGORY FILTER
            # ------------------------------------------------

            if category:

                if (
                    product_category.lower()
                    != str(category).strip().lower()
                ):

                    continue

            # ------------------------------------------------
            # RATING
            # ------------------------------------------------

            rating = row.get(
                "average_rating"
            )

            try:

                if pd.isna(rating):

                    rating = None

                else:

                    rating = float(
                        rating
                    )

            except Exception:

                rating = None

            # ------------------------------------------------
            # MINIMUM RATING FILTER
            # ------------------------------------------------

            if min_rating is not None:

                if rating is None:

                    continue

                if rating < float(
                    min_rating
                ):

                    continue

            # ------------------------------------------------
            # PRICE
            # ------------------------------------------------

            price = row.get(
                "price"
            )

            try:

                if pd.isna(price):

                    price = None

                else:

                    price = float(
                        price
                    )

            except Exception:

                price = None

            # ------------------------------------------------
            # MAXIMUM PRICE FILTER
            # ------------------------------------------------

            if max_price is not None:

                if price is None:

                    continue

                if price > float(
                    max_price
                ):

                    continue

            # ------------------------------------------------
            # TITLE
            # ------------------------------------------------

            title = row.get(
                "title",
                ""
            )

            if pd.isna(title):

                title = ""

            title = str(
                title
            )

            # ------------------------------------------------
            # RATING COUNT
            # ------------------------------------------------

            rating_number = row.get(
                "rating_number"
            )

            try:

                if pd.isna(
                    rating_number
                ):

                    rating_number = None

                else:

                    rating_number = int(
                        float(
                            rating_number
                        )
                    )

            except Exception:

                rating_number = None

            # ------------------------------------------------
            # BRAND / STORE
            # ------------------------------------------------

            brand = row.get(
                "store",
                ""
            )

            if pd.isna(brand):

                brand = ""

            brand = str(
                brand
            )

            # ------------------------------------------------
            # IMAGE
            # ------------------------------------------------

            image_data = row.get(
                "images"
            )

            image_url = (
                self.extract_image_url(
                    image_data
                )
            )

            # ------------------------------------------------
            # SIMILARITY
            # ------------------------------------------------

            similarity = float(
                scores[0][rank]
            )

            if not math.isfinite(
                similarity
            ):

                similarity = 0.0

            # ------------------------------------------------
            # RECOMMENDATION REASON
            # ------------------------------------------------

            reason_parts = [
                f"Semantically similar to '{query}'"
            ]

            if category:

                reason_parts.append(
                    f"Category: {product_category}"
                )

            if min_rating is not None:

                reason_parts.append(
                    f"Rating ≥ {min_rating}"
                )

            if max_price is not None:

                reason_parts.append(
                    f"Price ≤ {max_price}"
                )

            reason = " | ".join(
                reason_parts
            )

            # ------------------------------------------------
            # RESULT
            # ------------------------------------------------

            results.append({

                "product_id":
                    product_id,

                "title":
                    title,

                "price":
                    price,

                "rating":
                    rating,

                "rating_number":
                    rating_number,

                "brand":
                    brand,

                "category":
                    product_category,

                "similarity":
                    similarity,

                "images":
                    image_url,

                "image_url":
                    image_url,

                "reason":
                    reason
            })

        # ----------------------------------------------------
        # SORT BY SIMILARITY
        # ----------------------------------------------------

        results.sort(
            key=lambda x:
                x["similarity"],
            reverse=True
        )

        # ----------------------------------------------------
        # ASSIGN FINAL RANKS
        # ----------------------------------------------------

        results = results[
            :top_k
        ]

        for rank, result in enumerate(
            results,
            start=1
        ):

            result["rank"] = rank

        return results
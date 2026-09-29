from pathlib import Path
import ast
import io
import math

import faiss
import numpy as np
import pandas as pd

from PIL import Image

from sentence_transformers import SentenceTransformer

import torch
from torchvision.models import resnet50, ResNet50_Weights


class RetrievalService:

    def __init__(self):

        # ====================================================
        # PROJECT ROOT
        # ====================================================

        project_root = (
            Path(__file__)
            .resolve()
            .parents[3]
        )

        # ====================================================
        # FILE PATHS
        # ====================================================

        self.index_path = (
            project_root
            / "index"
            / "three_modal_product_index.faiss"
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

        self.text_projection_path = (
            project_root
            / "data"
            / "embeddings"
            / "text_projection.npy"
        )

        # NEW:
        # Image projection used during three-modal fusion
        self.image_projection_path = (
            project_root
            / "data"
            / "embeddings"
            / "image_projection.npy"
        )

        self.reviews_path = (
            project_root
            / "data"
            / "processed"
            / "reviews_multicategory_sentiment.csv"
        )

        # ====================================================
        # HEADER
        # ====================================================

        print()
        print("=" * 70)
        print("LOADING 3-MODAL RETRIEVAL SYSTEM")
        print("=" * 70)

        # ====================================================
        # CHECK REQUIRED FILES
        # ====================================================

        required_files = [
            self.index_path,
            self.product_ids_path,
            self.products_path,
            self.text_projection_path,
            self.image_projection_path,
        ]

        for file_path in required_files:

            if not file_path.exists():

                raise FileNotFoundError(
                    f"Required file not found:\n{file_path}"
                )

        # ====================================================
        # LOAD FAISS INDEX
        # ====================================================

        print()
        print("Loading FAISS index...")

        self.index = faiss.read_index(
            str(self.index_path)
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
            self.product_ids_path
        )

        self.product_ids["product_id"] = (
            self.product_ids["product_id"]
            .astype(str)
            .str.strip()
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
            self.products_path
        )

        self.products["product_id"] = (
            self.products["product_id"]
            .astype(str)
            .str.strip()
        )

        print(
            "Products:",
            len(self.products)
        )

        # ====================================================
        # LOAD TEXT PROJECTION
        # ====================================================

        print()
        print("Loading text projection...")

        self.text_projection = np.load(
            self.text_projection_path
        ).astype(
            np.float32
        )

        print(
            "Text projection:",
            self.text_projection.shape
        )

        # ====================================================
        # LOAD IMAGE PROJECTION
        # ====================================================

        print()
        print("Loading image projection...")

        self.image_projection = np.load(
            self.image_projection_path
        ).astype(
            np.float32
        )

        print(
            "Image projection:",
            self.image_projection.shape
        )

        # ====================================================
        # LOAD RESNET50
        # ====================================================

        print()
        print("Loading ResNet50...")

        self.image_weights = (
            ResNet50_Weights.DEFAULT
        )

        self.image_model = resnet50(
            weights=self.image_weights
        )

        # Remove final classification layer.
        # Output becomes 2048-dimensional.
        self.image_model.fc = torch.nn.Identity()

        self.image_model.eval()

        # Use GPU if available.
        self.image_device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.image_model.to(
            self.image_device
        )

        self.image_transform = (
            self.image_weights.transforms()
        )

        print(
            "ResNet50 loaded."
        )

        print(
            "Image device:",
            self.image_device
        )

        # ====================================================
        # LOAD SENTENCE-BERT
        # ====================================================

        print()
        print("Loading Sentence-BERT...")

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

        print(
            "Sentence-BERT loaded."
        )

        # ====================================================
        # LOAD REVIEW STATISTICS
        # ====================================================

        self.review_stats = {}

        print()
        print("Loading review statistics...")

        if self.reviews_path.exists():

            reviews = pd.read_csv(
                self.reviews_path
            )

            print(
                "Reviews loaded:",
                len(reviews)
            )

            # ------------------------------------------------
            # Required columns
            # ------------------------------------------------

            required_review_columns = [
                "product_id",
                "rating",
                "sentiment",
            ]

            missing_columns = [
                column
                for column in required_review_columns
                if column not in reviews.columns
            ]

            if missing_columns:

                print(
                    "WARNING: Missing review columns:",
                    missing_columns
                )

                print(
                    "Review statistics will be disabled."
                )

            else:

                # --------------------------------------------
                # Clean product IDs
                # --------------------------------------------

                reviews["product_id"] = (
                    reviews["product_id"]
                    .astype(str)
                    .str.strip()
                )

                # --------------------------------------------
                # Clean ratings
                # --------------------------------------------

                reviews["rating"] = pd.to_numeric(
                    reviews["rating"],
                    errors="coerce"
                )

                # --------------------------------------------
                # Clean sentiment
                # --------------------------------------------

                reviews["sentiment"] = (
                    reviews["sentiment"]
                    .astype(str)
                    .str.upper()
                    .str.strip()
                )

                # --------------------------------------------
                # Group reviews by product
                # --------------------------------------------

                grouped_reviews = reviews.groupby(
                    "product_id"
                )

                for product_id, group in grouped_reviews:

                    total_reviews = len(group)

                    # ----------------------------------------
                    # Average review rating
                    # ----------------------------------------

                    average_review_rating = (
                        group["rating"].mean()
                    )

                    # ----------------------------------------
                    # Positive / negative count
                    # ----------------------------------------

                    positive_count = (
                        group["sentiment"]
                        .eq("POSITIVE")
                        .sum()
                    )

                    negative_count = (
                        group["sentiment"]
                        .eq("NEGATIVE")
                        .sum()
                    )

                    # ----------------------------------------
                    # Percentages
                    # ----------------------------------------

                    if total_reviews > 0:

                        positive_percentage = (
                            positive_count
                            / total_reviews
                            * 100
                        )

                        negative_percentage = (
                            negative_count
                            / total_reviews
                            * 100
                        )

                    else:

                        positive_percentage = 0.0
                        negative_percentage = 0.0

                    # ----------------------------------------
                    # Overall sentiment
                    # ----------------------------------------

                    if positive_percentage >= 60:

                        overall_sentiment = "Positive"

                    elif negative_percentage >= 60:

                        overall_sentiment = "Negative"

                    else:

                        overall_sentiment = "Mixed"

                    # ----------------------------------------
                    # Save statistics
                    # ----------------------------------------

                    self.review_stats[
                        product_id
                    ] = {

                        "review_count":
                            int(total_reviews),

                        "average_review_rating":
                            self.safe_float(
                                average_review_rating
                            ),

                        "positive_review_percentage":
                            round(
                                float(
                                    positive_percentage
                                ),
                                2
                            ),

                        "negative_review_percentage":
                            round(
                                float(
                                    negative_percentage
                                ),
                                2
                            ),

                        "overall_sentiment":
                            overall_sentiment,
                    }

            print(
                "Products with review statistics:",
                len(self.review_stats)
            )

        else:

            print(
                "WARNING: Review sentiment file not found:"
            )

            print(
                self.reviews_path
            )

        # ====================================================
        # PRODUCT LOOKUP
        # ====================================================

        self.product_lookup = (
            self.products
            .set_index("product_id")
            .to_dict(
                orient="index"
            )
        )

        # ====================================================
        # FINAL STATUS
        # ====================================================

        print()
        print("=" * 70)
        print("3-MODAL RETRIEVAL SYSTEM READY")
        print("=" * 70)
        print()


    # ========================================================
    # SAFE FLOAT
    # ========================================================

    @staticmethod
    def safe_float(value):

        try:

            if value is None:
                return None

            value = float(value)

            if math.isfinite(value):
                return value

            return None

        except (
            TypeError,
            ValueError
        ):

            return None


    # ========================================================
    # SAFE STRING
    # ========================================================

    @staticmethod
    def safe_string(value):

        if value is None:
            return ""

        try:

            if pd.isna(value):
                return ""

        except Exception:
            pass

        return str(value)


    # ========================================================
    # EXTRACT IMAGE URL
    # ========================================================

    @staticmethod
    def extract_image_url(images):

        if images is None:
            return ""

        # ----------------------------------------------------
        # Handle NaN
        # ----------------------------------------------------

        try:

            if pd.isna(images):
                return ""

        except Exception:
            pass

        # ----------------------------------------------------
        # Direct URL / string representation
        # ----------------------------------------------------

        if isinstance(images, str):

            text = images.strip()

            if not text:
                return ""

            if (
                text.startswith("http://")
                or
                text.startswith("https://")
            ):

                return text

            # Try parsing string representation
            try:

                parsed = ast.literal_eval(
                    text
                )

                return (
                    RetrievalService
                    .extract_image_url(
                        parsed
                    )
                )

            except Exception:

                return ""

        # ----------------------------------------------------
        # Dictionary
        # ----------------------------------------------------

        if isinstance(images, dict):

            # Prefer highest quality image
            for key in [
                "hi_res",
                "large",
                "thumb",
            ]:

                value = images.get(
                    key
                )

                if (
                    isinstance(value, str)
                    and
                    (
                        value.startswith("http://")
                        or
                        value.startswith("https://")
                    )
                ):

                    return value

            return ""

        # ----------------------------------------------------
        # List
        # ----------------------------------------------------

        if isinstance(images, list):

            for item in images:

                result = (
                    RetrievalService
                    .extract_image_url(
                        item
                    )
                )

                if result:
                    return result

        return ""


    # ========================================================
    # TEXT EMBEDDING
    # ========================================================

    def encode_text(self, query):

        query = str(
            query
        ).strip()

        if not query:
            return None

        # SBERT
        embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        ).astype(
            np.float32
        )

        # 384 → 256
        embedding = (
            embedding
            @ self.text_projection
        ).astype(
            np.float32
        )

        # Normalize
        norm = np.linalg.norm(
            embedding,
            axis=1,
            keepdims=True
        )

        norm[norm == 0] = 1.0

        embedding = (
            embedding
            / norm
        ).astype(
            np.float32
        )

        return embedding


    # ========================================================
    # IMAGE EMBEDDING
    # ========================================================

    def encode_image(self, image_input):

        """
        Convert an uploaded image into:

        Image
          ↓
        ResNet50
          ↓
        2048 dimensions
          ↓
        Image projection
          ↓
        256 dimensions
          ↓
        Normalized vector
        """

        # ----------------------------------------------------
        # Read image
        # ----------------------------------------------------

        if isinstance(
            image_input,
            bytes
        ):

            image = Image.open(
                io.BytesIO(
                    image_input
                )
            )

        elif isinstance(
            image_input,
            Image.Image
        ):

            image = image_input

        else:

            image = Image.open(
                image_input
            )

        # ----------------------------------------------------
        # Convert to RGB
        # ----------------------------------------------------

        image = image.convert(
            "RGB"
        )

        # ----------------------------------------------------
        # ResNet preprocessing
        # ----------------------------------------------------

        tensor = self.image_transform(
            image
        )

        tensor = tensor.unsqueeze(
            0
        )

        tensor = tensor.to(
            self.image_device
        )

        # ----------------------------------------------------
        # ResNet50 inference
        # ----------------------------------------------------

        with torch.no_grad():

            embedding = (
                self.image_model(
                    tensor
                )
            )

        # ----------------------------------------------------
        # Convert to NumPy
        # ----------------------------------------------------

        embedding = (
            embedding
            .detach()
            .cpu()
            .numpy()
            .astype(
                np.float32
            )
        )

        # ----------------------------------------------------
        # Normalize 2048-D vector
        # ----------------------------------------------------

        norm = np.linalg.norm(
            embedding,
            axis=1,
            keepdims=True
        )

        norm[norm == 0] = 1.0

        embedding = (
            embedding
            / norm
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # Project 2048 → 256
        # ----------------------------------------------------

        embedding = (
            embedding
            @ self.image_projection
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # Normalize projected vector
        # ----------------------------------------------------

        norm = np.linalg.norm(
            embedding,
            axis=1,
            keepdims=True
        )

        norm[norm == 0] = 1.0

        embedding = (
            embedding
            / norm
        ).astype(
            np.float32
        )

        return embedding


    # ========================================================
    # DETERMINE SEARCH K
    # ========================================================

    def get_search_k(
        self,
        top_k,
        category=None,
        min_rating=None,
        max_price=None
    ):

        total_vectors = (
            self.index.ntotal
        )

        # Search everything when filters are active.
        if (
            category is not None
            or
            min_rating is not None
            or
            max_price is not None
        ):

            return total_vectors

        return min(
            max(
                top_k * 5,
                50
            ),
            total_vectors
        )


    # ========================================================
    # SEARCH FAISS
    # ========================================================

    def search_embedding(
        self,
        query_embedding,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None,
        search_mode="multimodal"
    ):

        search_k = self.get_search_k(
            top_k=top_k,
            category=category,
            min_rating=min_rating,
            max_price=max_price
        )

        # ----------------------------------------------------
        # FAISS
        # ----------------------------------------------------

        distances, indices = (
            self.index.search(
                query_embedding,
                search_k
            )
        )

        # ----------------------------------------------------
        # Results
        # ----------------------------------------------------

        results = []

        for score, index in zip(
            distances[0],
            indices[0]
        ):

            # Invalid index
            if index < 0:
                continue

            if index >= len(
                self.product_ids
            ):
                continue

            # ------------------------------------------------
            # Product ID
            # ------------------------------------------------

            product_id = (
                self.product_ids
                .iloc[index]
                ["product_id"]
            )

            product_id = str(
                product_id
            ).strip()

            # ------------------------------------------------
            # Product metadata
            # ------------------------------------------------

            product = (
                self.product_lookup
                .get(product_id)
            )

            if product is None:
                continue

            # =================================================
            # CATEGORY FILTER
            # =================================================

            product_category = (
                self.safe_string(
                    product.get(
                        "main_category",
                        ""
                    )
                )
            )

            if (
                category is not None
                and
                category.strip()
            ):

                if (
                    product_category.lower()
                    !=
                    category.strip().lower()
                ):

                    continue

            # =================================================
            # RATING
            # =================================================

            rating_value = (
                self.safe_float(
                    product.get(
                        "average_rating"
                    )
                )
            )

            if (
                min_rating is not None
            ):

                if (
                    rating_value is None
                    or
                    rating_value
                    <
                    float(min_rating)
                ):

                    continue

            # =================================================
            # PRICE
            # =================================================

            price_value = (
                self.safe_float(
                    product.get(
                        "price"
                    )
                )
            )

            if (
                max_price is not None
            ):

                if (
                    price_value is None
                    or
                    price_value
                    >
                    float(max_price)
                ):

                    continue

            # =================================================
            # RATING NUMBER
            # =================================================

            rating_number = (
                self.safe_float(
                    product.get(
                        "rating_number"
                    )
                )
            )

            if rating_number is not None:

                rating_number = int(
                    rating_number
                )

            # =================================================
            # IMAGE
            # =================================================

            image_url = (
                self.extract_image_url(
                    product.get(
                        "images"
                    )
                )
            )

            # =================================================
            # SIMILARITY
            # =================================================

            similarity = (
                self.safe_float(
                    score
                )
            )

            # =================================================
            # REVIEW STATISTICS
            # =================================================

            review_info = (
                self.review_stats.get(
                    product_id,
                    {
                        "review_count": 0,
                        "average_review_rating": None,
                        "positive_review_percentage": 0.0,
                        "negative_review_percentage": 0.0,
                        "overall_sentiment": "Unknown",
                    }
                )
            )

            # =================================================
            # RECOMMENDATION REASON
            # =================================================

            sentiment = (
                review_info[
                    "overall_sentiment"
                ]
            )

            positive_percentage = (
                review_info[
                    "positive_review_percentage"
                ]
            )

            # ------------------------------------------------
            # Different explanation depending on search mode
            # ------------------------------------------------

            if (
                search_mode
                ==
                "image"
            ):

                if sentiment == "Positive":

                    reason = (
                        "Visually similar to "
                        "your uploaded product, "
                        "with positive customer "
                        f"reviews "
                        f"({positive_percentage:.0f}% positive)."
                    )

                else:

                    reason = (
                        "Visually similar to "
                        "your uploaded product "
                        "based on the AI image "
                        "representation."
                    )

            elif (
                search_mode
                ==
                "text_image"
            ):

                if sentiment == "Positive":

                    reason = (
                        "Strong text and visual "
                        "similarity, supported by "
                        "positive customer reviews "
                        f"({positive_percentage:.0f}% positive)."
                    )

                else:

                    reason = (
                        "Strong match across your "
                        "text query and uploaded "
                        "product image."
                    )

            elif (
                search_mode
                ==
                "text"
            ):

                if sentiment == "Positive":

                    reason = (
                        "Strong semantic match "
                        "with your search and "
                        "positive customer reviews "
                        f"({positive_percentage:.0f}% positive)."
                    )

                else:

                    reason = (
                        "Strong semantic match "
                        "with your search."
                    )

            else:

                if sentiment == "Positive":

                    reason = (
                        "Strong match across "
                        "product text and visual "
                        "features, with positive "
                        "customer reviews "
                        f"({positive_percentage:.0f}% positive)."
                    )

                elif sentiment == "Negative":

                    reason = (
                        "Strong match across "
                        "product text and visual "
                        "features, although "
                        "customer review sentiment "
                        "is mostly negative."
                    )

                elif sentiment == "Mixed":

                    reason = (
                        "Strong match across "
                        "product text, visual "
                        "features, and mixed "
                        "customer reviews."
                    )

                else:

                    reason = (
                        "Recommended using "
                        "product text, visual "
                        "features, and customer "
                        "review information."
                    )

            # =================================================
            # FINAL RESULT
            # =================================================

            result = {

                "product_id":
                    product_id,

                "title":
                    self.safe_string(
                        product.get(
                            "title",
                            ""
                        )
                    ),

                "price":
                    price_value,

                "rating":
                    rating_value,

                "rating_number":
                    rating_number,

                "brand":
                    self.safe_string(
                        product.get(
                            "store",
                            ""
                        )
                    ),

                "category":
                    product_category,

                "similarity":
                    similarity,

                "image_url":
                    image_url,

                # --------------------------------------------
                # Review information
                # --------------------------------------------

                "review_count":
                    review_info[
                        "review_count"
                    ],

                "average_review_rating":
                    review_info[
                        "average_review_rating"
                    ],

                "positive_review_percentage":
                    review_info[
                        "positive_review_percentage"
                    ],

                "negative_review_percentage":
                    review_info[
                        "negative_review_percentage"
                    ],

                "overall_sentiment":
                    review_info[
                        "overall_sentiment"
                    ],

                # --------------------------------------------
                # Search mode
                # --------------------------------------------

                "search_mode":
                    search_mode,

                # --------------------------------------------
                # Explanation
                # --------------------------------------------

                "reason":
                    reason,
            }

            results.append(
                result
            )

            # =================================================
            # TOP-K
            # =================================================

            if len(results) >= top_k:

                break

        return results


    # ========================================================
    # TEXT SEARCH
    # ========================================================

    def search(
        self,
        query,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None
    ):

        query = str(
            query
        ).strip()

        if not query:
            return []

        query_embedding = (
            self.encode_text(
                query
            )
        )

        if query_embedding is None:
            return []

        return self.search_embedding(
            query_embedding=query_embedding,
            top_k=top_k,
            category=category,
            min_rating=min_rating,
            max_price=max_price,
            search_mode="text"
        )


    # ========================================================
    # IMAGE SEARCH
    # ========================================================

    def search_by_image(
        self,
        image_input,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None
    ):

        image_embedding = (
            self.encode_image(
                image_input
            )
        )

        return self.search_embedding(
            query_embedding=image_embedding,
            top_k=top_k,
            category=category,
            min_rating=min_rating,
            max_price=max_price,
            search_mode="image"
        )


    # ========================================================
    # TEXT + IMAGE SEARCH
    # ========================================================

    def search_multimodal(
        self,
        query=None,
        image_input=None,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None,
        text_weight=0.5,
        image_weight=0.5
    ):

        has_text = (
            query is not None
            and
            str(query).strip()
        )

        has_image = (
            image_input is not None
        )

        # ----------------------------------------------------
        # Nothing supplied
        # ----------------------------------------------------

        if (
            not has_text
            and
            not has_image
        ):

            return []

        # ----------------------------------------------------
        # Text only
        # ----------------------------------------------------

        if (
            has_text
            and
            not has_image
        ):

            return self.search(
                query=query,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price
            )

        # ----------------------------------------------------
        # Image only
        # ----------------------------------------------------

        if (
            has_image
            and
            not has_text
        ):

            return self.search_by_image(
                image_input=image_input,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price
            )

        # ----------------------------------------------------
        # TEXT + IMAGE
        # ----------------------------------------------------

        text_embedding = (
            self.encode_text(
                query
            )
        )

        image_embedding = (
            self.encode_image(
                image_input
            )
        )

        # ----------------------------------------------------
        # Weighted multimodal query
        # ----------------------------------------------------

        fused_embedding = (
            (
                text_weight
                * text_embedding
            )
            +
            (
                image_weight
                * image_embedding
            )
        ).astype(
            np.float32
        )

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        norm = np.linalg.norm(
            fused_embedding,
            axis=1,
            keepdims=True
        )

        norm[norm == 0] = 1.0

        fused_embedding = (
            fused_embedding
            / norm
        ).astype(
            np.float32
        )

        return self.search_embedding(
            query_embedding=fused_embedding,
            top_k=top_k,
            category=category,
            min_rating=min_rating,
            max_price=max_price,
            search_mode="text_image"
        )
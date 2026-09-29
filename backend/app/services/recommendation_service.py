from .retrieval_service import RetrievalService


class RecommendationService:

    def __init__(self):

        self.retrieval_service = (
            RetrievalService()
        )


    # ========================================================
    # TEXT RECOMMENDATION
    # ========================================================

    def recommend(
        self,
        query,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None
    ):

        results = (
            self.retrieval_service.search(
                query=query,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price
            )
        )

        return results


    # ========================================================
    # IMAGE RECOMMENDATION
    # ========================================================

    def recommend_by_image(
        self,
        image_bytes,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None
    ):

        results = (
            self.retrieval_service.search_by_image(
                image_input=image_bytes,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price
            )
        )

        return results


    # ========================================================
    # TEXT + IMAGE MULTIMODAL RECOMMENDATION
    # ========================================================

    def recommend_multimodal(
        self,
        query,
        image_bytes,
        top_k=10,
        category=None,
        min_rating=None,
        max_price=None,
        text_weight=0.5,
        image_weight=0.5
    ):

        results = (
            self.retrieval_service.search_multimodal(
                query=query,
                image_input=image_bytes,
                top_k=top_k,
                category=category,
                min_rating=min_rating,
                max_price=max_price,
                text_weight=text_weight,
                image_weight=image_weight
            )
        )

        return results
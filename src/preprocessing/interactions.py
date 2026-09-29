import pandas as pd


def build_interactions(
    reviews_df: pd.DataFrame
) -> pd.DataFrame:

    interactions = reviews_df[
        [
            "user_id",
            "product_id",
            "rating",
            "timestamp"
        ]
    ].copy()

    interactions["interaction_type"] = "rating"

    return interactions.reset_index(drop=True)
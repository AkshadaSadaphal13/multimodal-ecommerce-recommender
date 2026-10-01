"""Audit available recommendation ground truth before reporting metrics.

Current interactions.csv uses synthetic IDs (for example p001) that do not
join to the Amazon product catalog. Product reviews identify the reviewed item,
but do not provide query-to-relevant-item judgments for image or multimodal
retrieval. This script records those coverage checks and leaves unsupported
metrics blank instead of presenting fabricated scores.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation_results.csv"

products = pd.read_csv(ROOT / "data/processed/products_aligned.csv", usecols=["product_id"])
product_ids = set(products.product_id.astype(str))
interactions_path = ROOT / "data/processed/interactions.csv"
interactions = pd.read_csv(interactions_path) if interactions_path.exists() else pd.DataFrame()
reviews = pd.read_csv(ROOT / "data/processed/reviews_multicategory_sentiment.csv", usecols=["product_id", "rating"])
review_ids = set(reviews.product_id.dropna().astype(str))
interaction_ids = set(interactions.product_id.dropna().astype(str)) if "product_id" in interactions else set()
joinable_interactions = len(interaction_ids & product_ids)
joinable_review_products = len(review_ids & product_ids)

rows = []
reason = (
    f"Recommendation metrics not computed: interactions join {joinable_interactions}/"
    f"{len(interaction_ids)} product IDs; review rows identify {joinable_review_products} catalog items "
    "but do not define query relevance. Reviews alone are not valid retrieval ground truth."
)
for model in ("text_only", "image_only", "text_image", "text_image_review"):
    for k in (5, 10):
        rows.append({"model": model, "k": k, "precision": None, "recall": None,
                     "ndcg": None, "hit_rate": None, "status": reason})
pd.DataFrame(rows).to_csv(OUT, index=False)
print("Recommendation evaluation data audit")
print(f"Catalog products: {len(product_ids)}")
print(f"Interactions joining to catalog: {joinable_interactions}/{len(interaction_ids)}")
print(f"Review products joining to catalog: {joinable_review_products}/{len(review_ids)}")
print(reason)
print(f"Wrote auditable result template: {OUT}")

"""Evaluate model sentiment against rating-derived weak labels (not human truth)."""
from pathlib import Path
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "data/processed/reviews_multicategory_sentiment.csv"
df = pd.read_csv(path)
df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
df["sentiment"] = df["sentiment"].astype(str).str.upper().str.strip()
# Exclude neutral 3-star reviews; ratings 4-5 are positive, 1-2 negative.
df = df[df.rating.notna() & df.rating.ne(3) & df.sentiment.isin(["POSITIVE", "NEGATIVE"])].copy()
df["rating_label"] = df.rating.map(lambda value: "POSITIVE" if value >= 4 else "NEGATIVE")
y_true, y_pred = df.rating_label, df.sentiment
precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", pos_label="POSITIVE", zero_division=0)
metrics = {"n": len(df), "accuracy": accuracy_score(y_true, y_pred), "precision": precision, "recall": recall, "f1": f1,
           "label_method": "weak proxy: rating >=4 positive, <=2 negative; 3-star excluded"}
pd.DataFrame([metrics]).to_csv(ROOT / "sentiment_evaluation_results.csv", index=False)
print("Sentiment evaluation against rating-derived weak labels")
print(f"N={metrics['n']} Accuracy={metrics['accuracy']:.4f} Precision={precision:.4f} Recall={recall:.4f} F1={f1:.4f}")
print("These are agreement scores against rating-derived proxy labels, not independently annotated sentiment truth.")

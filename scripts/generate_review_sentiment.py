import pandas as pd
from transformers import pipeline
from tqdm import tqdm

INPUT_FILE = "data/processed/reviews_multicategory.csv"
OUTPUT_FILE = "data/processed/reviews_multicategory_sentiment.csv"

print("=" * 70)
print("REVIEW SENTIMENT ANALYSIS")
print("=" * 70)

# Load reviews
df = pd.read_csv(INPUT_FILE)

print(f"Reviews loaded: {len(df)}")

# Remove missing review text
df = df.dropna(subset=["review_text"]).copy()

df["review_text"] = df["review_text"].astype(str).str.strip()

df = df[df["review_text"] != ""]

print(f"Valid reviews: {len(df)}")

# Load pretrained sentiment model
print("\nLoading sentiment model...")

sentiment_model = pipeline(
    "sentiment-analysis",
    model="distilbert-base-uncased-finetuned-sst-2-english",
    truncation=True,
    max_length=512
)

print("Model loaded.")

# Process reviews
sentiments = []
scores = []

print("\nRunning sentiment analysis...")

for text in tqdm(
    df["review_text"].tolist(),
    desc="Processing reviews"
):

    result = sentiment_model(text)[0]

    sentiments.append(result["label"])
    scores.append(result["score"])

# Save results
df["sentiment"] = sentiments
df["sentiment_score"] = scores

df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 70)
print("SENTIMENT ANALYSIS COMPLETE")
print("=" * 70)

print(f"Total reviews: {len(df)}")

print("\nSentiment distribution:")
print(df["sentiment"].value_counts())

print("\nAverage sentiment confidence:")
print(df["sentiment_score"].mean())

print("\nSaved to:")
print(OUTPUT_FILE)

print("=" * 70)
from pathlib import Path
import pandas as pd
import ast
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multicategory_real.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multimodal.csv"
)


def extract_image_url(value):

    if value is None:
        return ""

    if isinstance(value, float):
        try:
            if pd.isna(value):
                return ""
        except:
            pass

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return ""

        try:
            parsed = json.loads(value)
            return extract_image_url(parsed)
        except:
            pass

        try:
            parsed = ast.literal_eval(value)
            return extract_image_url(parsed)
        except:
            pass

        if value.startswith("http"):
            return value

        return ""

    if isinstance(value, dict):

        for key in ["hi_res", "large", "thumb"]:

            url = value.get(key)

            if (
                isinstance(url, str)
                and url.startswith("http")
            ):
                return url

        return ""

    if isinstance(value, list):

        for item in value:

            url = extract_image_url(item)

            if url:
                return url

    return ""


print("Loading dataset...")

df = pd.read_csv(INPUT_PATH)

print("Original products:", len(df))


# Extract usable image URL
df["image_url"] = df["images"].apply(
    extract_image_url
)


# Keep products with valid images
df = df[
    df["image_url"].str.startswith("http")
].copy()


# Remove duplicate products
df = df.drop_duplicates(
    subset=["product_id"]
).reset_index(drop=True)


# Create combined text for SBERT
df["combined_text"] = (
    df["title"].fillna("").astype(str)
    + " "
    + df["features"].fillna("").astype(str)
    + " "
    + df["description"].fillna("").astype(str)
)


df.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)


print()
print("=" * 60)
print("MULTIMODAL DATASET CREATED")
print("=" * 60)

print()

print("Products with images:", len(df))

print()

print("Category distribution:")

print(
    df["main_category"]
    .value_counts()
)

print()

print("Columns:")

print(
    df.columns.tolist()
)

print()

print("Saved to:")

print(OUTPUT_PATH)
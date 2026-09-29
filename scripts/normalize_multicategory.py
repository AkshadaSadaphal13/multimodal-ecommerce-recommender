from pathlib import Path
import pandas as pd
import hashlib


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multicategory.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multicategory_final.csv"
)


# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(
    INPUT_PATH
)

print("=" * 70)
print("NORMALIZING MULTI-CATEGORY DATASET")
print("=" * 70)

print(
    "Input products:",
    len(df)
)

print(
    "Input columns:",
    df.columns.tolist()
)


# =========================================================
# CREATE PRODUCT ID
# =========================================================

def create_product_id(row):

    text = (
        str(row.get("main_category", ""))
        + "|"
        + str(row.get("title", ""))
        + "|"
        + str(row.get("store", ""))
    )

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()[:16]


df["product_id"] = df.apply(
    create_product_id,
    axis=1
)


# =========================================================
# CLEAN TITLE
# =========================================================

df["title"] = (
    df["title"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# =========================================================
# CLEAN CATEGORY
# =========================================================

df["main_category"] = (
    df["main_category"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# =========================================================
# CLEAN STORE / BRAND
# =========================================================

df["store"] = (
    df["store"]
    .fillna("")
    .astype(str)
    .str.strip()
)


# =========================================================
# PRICE
# =========================================================

df["price"] = pd.to_numeric(
    df["price"],
    errors="coerce"
)


# =========================================================
# RATING
# =========================================================

df["average_rating"] = pd.to_numeric(
    df["average_rating"],
    errors="coerce"
)


# =========================================================
# RATING NUMBER
# =========================================================

df["rating_number"] = pd.to_numeric(
    df["rating_number"],
    errors="coerce"
)


# =========================================================
# IMAGE COLUMN
# =========================================================

# The current raw Parquet does not contain
# image URLs, so create the column now.
#
# We will populate this later when connecting
# the image metadata.

df["images"] = None


# =========================================================
# DESCRIPTION
# =========================================================

df["description"] = (
    df["details"]
    .fillna("")
    .astype(str)
)


# =========================================================
# FEATURES
# =========================================================

df["features"] = ""


# =========================================================
# REMOVE DUPLICATES
# =========================================================

df = df.drop_duplicates(
    subset=["product_id"]
)


# =========================================================
# SELECT FINAL COLUMNS
# =========================================================

final_columns = [
    "product_id",
    "main_category",
    "title",
    "average_rating",
    "rating_number",
    "features",
    "description",
    "price",
    "images",
    "store",
    "details",
]


df = df[
    final_columns
]


# =========================================================
# SAVE
# =========================================================

df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# REPORT
# =========================================================

print("\n")
print("=" * 70)
print("NORMALIZATION COMPLETE")
print("=" * 70)

print(
    "Output:",
    OUTPUT_PATH
)

print(
    "Products:",
    len(df)
)

print(
    "\nColumns:"
)

print(
    df.columns.tolist()
)

print(
    "\nCategory distribution:"
)

print(
    df["main_category"].value_counts()
)

print(
    "\nSample:"
)

print(
    df[
        [
            "product_id",
            "main_category",
            "title",
            "price",
            "store"
        ]
    ]
    .head(5)
    .to_string(index=False)
)
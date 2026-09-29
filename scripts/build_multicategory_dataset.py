from pathlib import Path
import random

import pandas as pd
import pyarrow.parquet as pq


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "metadata"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multicategory.csv"
)


# =========================================================
# SETTINGS
# =========================================================

PRODUCTS_PER_CATEGORY = 500

RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# =========================================================
# COLUMNS WE NEED
# =========================================================

REQUIRED_COLUMNS = [
    "main_category",
    "title",
    "average_rating",
    "rating_number",
    "features",
    "description",
    "price",
    "images",
    "videos",
    "store",
    "categories",
    "details",
    "product_id",
]


# =========================================================
# FIND PARQUET FILES
# =========================================================

parquet_files = sorted(
    RAW_DIR.glob("*.parquet")
)

if not parquet_files:

    raise FileNotFoundError(
        f"No parquet files found in {RAW_DIR}"
    )


print("=" * 70)
print("MULTI-CATEGORY DATASET CREATION")
print("=" * 70)

print(
    f"Parquet files found: {len(parquet_files)}"
)

for file in parquet_files:

    print(
        f"  - {file.name}"
    )


# =========================================================
# STEP 1
# COUNT CATEGORIES
# =========================================================

print("\n")
print("=" * 70)
print("STEP 1: SCANNING CATEGORIES")
print("=" * 70)


category_counts = {}


for file_path in parquet_files:

    print(
        f"\nScanning: {file_path.name}"
    )

    parquet_file = pq.ParquetFile(
        file_path
    )

    print(
        "Row groups:",
        parquet_file.num_row_groups
    )

    for row_group_index in range(
        parquet_file.num_row_groups
    ):

        table = parquet_file.read_row_group(
            row_group_index,
            columns=["main_category"]
        )

        df = table.to_pandas()

        counts = (
            df["main_category"]
            .dropna()
            .astype(str)
            .str.strip()
            .value_counts()
        )

        for category, count in counts.items():

            category_counts[category] = (
                category_counts.get(
                    category,
                    0
                )
                + int(count)
            )


# =========================================================
# DISPLAY CATEGORY COUNTS
# =========================================================

category_series = pd.Series(
    category_counts
).sort_values(
    ascending=False
)

print("\n")
print("AVAILABLE CATEGORIES:")
print("-" * 70)

print(
    category_series.to_string()
)


# =========================================================
# STEP 2
# SELECT NON-FASHION CATEGORIES
# =========================================================

print("\n")
print("=" * 70)
print("STEP 2: SELECTING CATEGORIES")
print("=" * 70)


eligible_categories = []

for category, count in category_series.items():

    category_lower = category.lower()

    # Skip Fashion because current dataset
    # is already dominated by Fashion.

    if "fashion" in category_lower:

        continue

    # Need at least 500 products
    # for balanced sampling.

    if count >= PRODUCTS_PER_CATEGORY:

        eligible_categories.append(
            category
        )


# Take the 10 largest eligible categories

selected_categories = (
    eligible_categories[:10]
)


print(
    "\nSelected categories:"
)

for category in selected_categories:

    print(
        f"  {category}: "
        f"{category_counts[category]} available"
    )


if len(selected_categories) < 5:

    raise RuntimeError(
        "\nNot enough categories have "
        f"{PRODUCTS_PER_CATEGORY}+ products.\n"
        "Check the category output above."
    )


# =========================================================
# STEP 3
# READ PRODUCT DATA
# =========================================================

print("\n")
print("=" * 70)
print("STEP 3: COLLECTING PRODUCTS")
print("=" * 70)


# Dictionary:
#
# category -> list of dataframes

category_data = {
    category: []
    for category in selected_categories
}


for file_path in parquet_files:

    print(
        f"\nReading: {file_path.name}"
    )

    parquet_file = pq.ParquetFile(
        file_path
    )

    # Determine which required columns
    # actually exist in the file.

    available_columns = (
        parquet_file.schema.names
    )

    columns_to_read = [
        column
        for column in REQUIRED_COLUMNS
        if column in available_columns
    ]

    print(
        "Columns being read:",
        columns_to_read
    )

    for row_group_index in range(
        parquet_file.num_row_groups
    ):

        table = parquet_file.read_row_group(
            row_group_index,
            columns=columns_to_read
        )

        df = table.to_pandas()

        if "main_category" not in df.columns:
            continue

        # Clean category

        df["main_category"] = (
            df["main_category"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # Keep only selected categories

        df = df[
            df["main_category"].isin(
                selected_categories
            )
        ]

        if len(df) == 0:
            continue

        # Add data to each category

        for category in selected_categories:

            category_df = df[
                df["main_category"]
                == category
            ]

            if len(category_df) > 0:

                category_data[
                    category
                ].append(
                    category_df
                )


# =========================================================
# STEP 4
# SAMPLE PRODUCTS
# =========================================================

print("\n")
print("=" * 70)
print("STEP 4: BALANCING DATASET")
print("=" * 70)


final_parts = []


for category in selected_categories:

    if not category_data[category]:

        print(
            f"WARNING: No data for {category}"
        )

        continue

    category_df = pd.concat(
        category_data[category],
        ignore_index=True
    )

    # Remove duplicate products

    if "product_id" in category_df.columns:

        category_df = (
            category_df
            .drop_duplicates(
                subset=["product_id"]
            )
        )

    available = len(
        category_df
    )

    sample_size = min(
        PRODUCTS_PER_CATEGORY,
        available
    )

    sampled = (
        category_df
        .sample(
            n=sample_size,
            random_state=RANDOM_SEED
        )
    )

    print(
        f"{category}: "
        f"{available} available -> "
        f"{sample_size} selected"
    )

    final_parts.append(
        sampled
    )


# =========================================================
# COMBINE
# =========================================================

if not final_parts:

    raise RuntimeError(
        "No products were collected."
    )


final_df = pd.concat(
    final_parts,
    ignore_index=True
)


# =========================================================
# REMOVE DUPLICATES
# =========================================================

if "product_id" in final_df.columns:

    final_df = (
        final_df
        .drop_duplicates(
            subset=["product_id"]
        )
    )


# =========================================================
# SHUFFLE
# =========================================================

final_df = (
    final_df
    .sample(
        frac=1,
        random_state=RANDOM_SEED
    )
    .reset_index(drop=True)
)


# =========================================================
# SAVE
# =========================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


final_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# FINAL REPORT
# =========================================================

print("\n")
print("=" * 70)
print("DATASET CREATED SUCCESSFULLY")
print("=" * 70)

print(
    "Output:",
    OUTPUT_PATH
)

print(
    "Total products:",
    len(final_df)
)

print("\nCategory distribution:")

print(
    final_df[
        "main_category"
    ]
    .value_counts()
)


print("\nColumns:")

print(
    final_df.columns.tolist()
)


print("\nFirst 5 products:")

print(
    final_df.head()
)
from pathlib import Path
import json
import ast

import pandas as pd
from huggingface_hub import hf_hub_download


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multicategory_real.csv"
)


# ============================================================
# HUGGING FACE DATASET
# ============================================================

REPO_ID = "McAuley-Lab/Amazon-Reviews-2023"


# ============================================================
# CATEGORIES
# ============================================================

CATEGORIES = {
    "All_Beauty": "All Beauty",
    "Digital_Music": "Digital Music",
    "Gift_Cards": "Gift Cards",
    "Health_and_Personal_Care": "Health & Personal Care",
    "Video_Games": "Video Games",
}


# Number of products required from each category
TARGET_PER_CATEGORY = 500


# ============================================================
# HELPER: CLEAN VALUES
# ============================================================

def clean_value(value):
    """
    Convert lists, dictionaries, None and other values
    into CSV-friendly text.
    """

    if value is None:
        return ""

    # Handle NaN safely
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    # List / tuple
    if isinstance(value, (list, tuple)):

        return " ".join(
            str(x)
            for x in value
            if x is not None
        )

    # Dictionary
    if isinstance(value, dict):

        return json.dumps(
            value,
            ensure_ascii=False
        )

    return str(value).strip()


# ============================================================
# HELPER: EXTRACT IMAGE URL
# ============================================================

def extract_image_url(images):
    """
    Extract the best available Amazon product image URL.

    Amazon metadata normally contains something like:

    [
        {
            "thumb": "...",
            "large": "...",
            "hi_res": "..."
        }
    ]

    We prefer:

        hi_res
        large
        thumb
    """

    if images is None:
        return ""

    # --------------------------------------------------------
    # Case 1: empty value
    # --------------------------------------------------------

    if isinstance(images, float):

        try:
            if pd.isna(images):
                return ""
        except Exception:
            pass

    # --------------------------------------------------------
    # Case 2: string
    # --------------------------------------------------------

    if isinstance(images, str):

        images = images.strip()

        if not images:
            return ""

        # Direct URL
        if images.startswith("http"):

            return images

        # String representation of Python list/dict
        try:

            parsed = ast.literal_eval(images)

            return extract_image_url(parsed)

        except Exception:

            return ""

    # --------------------------------------------------------
    # Case 3: dictionary
    # --------------------------------------------------------

    if isinstance(images, dict):

        for key in [
            "hi_res",
            "large",
            "thumb"
        ]:

            url = images.get(key)

            if (
                isinstance(url, str)
                and url.startswith("http")
            ):

                return url

        return ""

    # --------------------------------------------------------
    # Case 4: list / tuple
    # --------------------------------------------------------

    if isinstance(images, (list, tuple)):

        for image in images:

            # Each item is normally a dictionary
            if isinstance(image, dict):

                for key in [
                    "hi_res",
                    "large",
                    "thumb"
                ]:

                    url = image.get(key)

                    if (
                        isinstance(url, str)
                        and url.startswith("http")
                    ):

                        return url

            # In case an item is itself a string
            elif isinstance(image, str):

                if image.startswith("http"):

                    return image

        return ""

    return ""


# ============================================================
# HELPER: CHECK IMAGE
# ============================================================

def has_valid_image(images):
    """
    Return True if the product has at least one usable
    Amazon image URL.
    """

    image_url = extract_image_url(images)

    return bool(image_url)


# ============================================================
# PROCESS ONE CATEGORY
# ============================================================

def process_category(
    category_name,
    display_name
):

    print()
    print("=" * 70)
    print(f"PROCESSING: {display_name}")
    print("=" * 70)

    # --------------------------------------------------------
    # Hugging Face file path
    # --------------------------------------------------------

    filename = (
        f"raw/meta_categories/"
        f"meta_{category_name}.jsonl"
    )

    print()
    print("Metadata file:")
    print(filename)

    # --------------------------------------------------------
    # Download using normal HF cache
    #
    # IMPORTANT:
    # We intentionally DO NOT use local_dir here.
    # This avoids the Windows .cache error.
    # --------------------------------------------------------

    try:

        local_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            repo_type="dataset"
        )

    except Exception as e:

        print()
        print(
            f"ERROR downloading {display_name}:"
        )

        print(e)

        print(
            f"Skipping {display_name}..."
        )

        return []

    print()
    print("Downloaded / cached file:")
    print(local_path)

    # --------------------------------------------------------
    # Read JSONL
    # --------------------------------------------------------

    products = []

    print()
    print(
        f"Reading products "
        f"(target = {TARGET_PER_CATEGORY})..."
    )

    try:

        with open(
            local_path,
            "r",
            encoding="utf-8"
        ) as f:

            for line_number, line in enumerate(
                f,
                start=1
            ):

                # Stop once enough products are found
                if len(products) >= TARGET_PER_CATEGORY:
                    break

                line = line.strip()

                if not line:
                    continue

                # ------------------------------------------------
                # Parse JSON
                # ------------------------------------------------

                try:

                    item = json.loads(line)

                except json.JSONDecodeError:

                    continue

                # ------------------------------------------------
                # Product ID
                # ------------------------------------------------

                product_id = item.get(
                    "parent_asin"
                )

                if not product_id:
                    continue

                product_id = str(
                    product_id
                ).strip()

                if not product_id:
                    continue

                # ------------------------------------------------
                # Title
                # ------------------------------------------------

                title = item.get(
                    "title"
                )

                if not title:
                    continue

                title = clean_value(
                    title
                )

                if not title:
                    continue

                # ------------------------------------------------
                # Images
                # ------------------------------------------------

                images = item.get(
                    "images"
                )

                image_url = extract_image_url(
                    images
                )

                # We need real image URLs
                if not image_url:
                    continue

                # ------------------------------------------------
                # Build product record
                # ------------------------------------------------

                product = {

                    "product_id":
                        product_id,

                    "main_category":
                        display_name,

                    "title":
                        title,

                    "average_rating":
                        item.get(
                            "average_rating",
                            ""
                        ),

                    "rating_number":
                        item.get(
                            "rating_number",
                            ""
                        ),

                    "features":
                        clean_value(
                            item.get(
                                "features"
                            )
                        ),

                    "description":
                        clean_value(
                            item.get(
                                "description"
                            )
                        ),

                    "price":
                        item.get(
                            "price",
                            ""
                        ),

                    # Preserve the complete image information
                    "images":
                        json.dumps(
                            images,
                            ensure_ascii=False
                        ),

                    "store":
                        clean_value(
                            item.get(
                                "store"
                            )
                        ),

                    "categories":
                        clean_value(
                            item.get(
                                "categories"
                            )
                        ),

                    "details":
                        clean_value(
                            item.get(
                                "details"
                            )
                        ),
                }

                products.append(
                    product
                )

                # ------------------------------------------------
                # Progress
                # ------------------------------------------------

                if len(products) % 100 == 0:

                    print(
                        f"Collected "
                        f"{len(products)} products..."
                    )

    except Exception as e:

        print()
        print(
            f"ERROR reading {display_name}:"
        )

        print(e)

        return products

    # --------------------------------------------------------
    # Category summary
    # --------------------------------------------------------

    print()
    print(
        f"Collected {len(products)} "
        f"products for {display_name}"
    )

    return products


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("BUILDING REAL MULTI-CATEGORY AMAZON DATASET")
    print("=" * 70)

    print()
    print(
        f"Target: "
        f"{TARGET_PER_CATEGORY} products/category"
    )

    print(
        f"Categories: "
        f"{len(CATEGORIES)}"
    )

    print()

    all_products = []

    # --------------------------------------------------------
    # Process every category
    # --------------------------------------------------------

    for category_name, display_name in CATEGORIES.items():

        products = process_category(
            category_name,
            display_name
        )

        all_products.extend(
            products
        )

    # --------------------------------------------------------
    # Check result
    # --------------------------------------------------------

    if not all_products:

        raise RuntimeError(
            "No products were collected. "
            "Please check the Hugging Face download "
            "and metadata format."
        )

    # --------------------------------------------------------
    # Create DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        all_products
    )

    # --------------------------------------------------------
    # Remove duplicate Amazon product IDs
    # --------------------------------------------------------

    before = len(df)

    df = df.drop_duplicates(
        subset=["product_id"]
    ).reset_index(drop=True)

    after = len(df)

    print()

    print(
        f"Removed {before - after} "
        f"duplicate products."
    )

    # --------------------------------------------------------
    # Save dataset
    # --------------------------------------------------------

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig"
    )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("DATASET CREATION COMPLETE")
    print("=" * 70)

    print()

    print(
        f"Total products: {len(df)}"
    )

    print()

    print(
        "Category distribution:"
    )

    print(
        df["main_category"]
        .value_counts()
        .to_string()
    )

    print()

    print(
        "Columns:"
    )

    print(
        df.columns.tolist()
    )

    # --------------------------------------------------------
    # Image statistics
    # --------------------------------------------------------

    valid_images = 0

    for value in df["images"]:

        if extract_image_url(value):

            valid_images += 1

    print()

    print(
        f"Products with valid images: "
        f"{valid_images}/{len(df)}"
    )

    print()

    print(
        "Sample products:"
    )

    print()

    print(
        df[
            [
                "product_id",
                "main_category",
                "title",
                "price"
            ]
        ]
        .head(5)
        .to_string(index=False)
    )

    print()

    print(
        "Saved to:"
    )

    print(
        OUTPUT_PATH
    )

    print()
    print("=" * 70)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
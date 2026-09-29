from pathlib import Path
import ast
import json
import io
import time

import numpy as np
import pandas as pd
import requests
from PIL import Image

import torch
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "products_multimodal.csv"
)

EMBEDDING_DIR = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
)

EMBEDDING_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_EMBEDDINGS = (
    EMBEDDING_DIR
    / "image_embeddings.npy"
)

OUTPUT_PRODUCT_IDS = (
    EMBEDDING_DIR
    / "image_product_ids.csv"
)

OUTPUT_STATUS = (
    EMBEDDING_DIR
    / "image_embedding_status.csv"
)


# ============================================================
# SETTINGS
# ============================================================

BATCH_SIZE = 16

IMAGE_SIZE = 224

REQUEST_TIMEOUT = 15

MAX_RETRIES = 2

USER_AGENT = (
    "Mozilla/5.0 "
    "(Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/153.0 Safari/537.36"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# IMAGE URL EXTRACTION
# ============================================================

def extract_image_url(value):

    if value is None:
        return ""

    # --------------------------------------------------------
    # NaN
    # --------------------------------------------------------

    if isinstance(value, float):

        try:

            if pd.isna(value):
                return ""

        except Exception:

            pass

    # --------------------------------------------------------
    # String
    # --------------------------------------------------------

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return ""

        # Direct URL
        if value.startswith("http"):

            return value

        # JSON
        try:

            parsed = json.loads(value)

            return extract_image_url(
                parsed
            )

        except Exception:

            pass

        # Python representation
        try:

            parsed = ast.literal_eval(value)

            return extract_image_url(
                parsed
            )

        except Exception:

            return ""

    # --------------------------------------------------------
    # Dictionary
    # --------------------------------------------------------

    if isinstance(value, dict):

        for key in [
            "hi_res",
            "large",
            "thumb"
        ]:

            url = value.get(key)

            if (
                isinstance(url, str)
                and url.startswith("http")
            ):

                return url

        return ""

    # --------------------------------------------------------
    # List
    # --------------------------------------------------------

    if isinstance(value, list):

        for item in value:

            url = extract_image_url(
                item
            )

            if url:

                return url

        return ""

    return ""


# ============================================================
# DOWNLOAD IMAGE
# ============================================================

def download_image(
    url,
    session
):

    if not url:

        return None

    for attempt in range(
        MAX_RETRIES + 1
    ):

        try:

            response = session.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers={
                    "User-Agent":
                        USER_AGENT
                }
            )

            if response.status_code != 200:

                continue

            image = Image.open(
                io.BytesIO(
                    response.content
                )
            )

            image = image.convert(
                "RGB"
            )

            return image

        except Exception:

            if attempt < MAX_RETRIES:

                time.sleep(
                    0.5
                )

    return None


# ============================================================
# MAIN
# ============================================================

print()
print("=" * 70)
print("RESNET50 IMAGE EMBEDDING GENERATION")
print("=" * 70)

print()

print(
    "Device:",
    DEVICE
)

print()

# ------------------------------------------------------------
# Load dataset
# ------------------------------------------------------------

print(
    "Loading product dataset..."
)

df = pd.read_csv(
    INPUT_PATH
)

print(
    f"Products loaded: {len(df)}"
)


# ------------------------------------------------------------
# Extract image URLs
# ------------------------------------------------------------

print()

print(
    "Extracting image URLs..."
)

df["image_url"] = df["images"].apply(
    extract_image_url
)

valid_url_count = (
    df["image_url"]
    .astype(str)
    .str.startswith("http")
    .sum()
)

print(
    f"Products with image URLs: "
    f"{valid_url_count}/{len(df)}"
)


# ============================================================
# LOAD RESNET50
# ============================================================

print()

print(
    "Loading pretrained ResNet50..."
)

weights = (
    ResNet50_Weights.DEFAULT
)

resnet = resnet50(
    weights=weights
)

# Remove final classification layer
model = nn.Sequential(
    *list(resnet.children())[:-1]
)

model = model.to(
    DEVICE
)

model.eval()

# Correct ImageNet preprocessing
preprocess = weights.transforms()

print(
    "ResNet50 loaded successfully."
)

print(
    "Feature dimension: 2048"
)


# ============================================================
# PROCESS IMAGES
# ============================================================

embeddings = []

successful_product_ids = []

status_records = []

session = requests.Session()

total = len(df)

print()

print(
    "Downloading and processing images..."
)

print(
    f"Total products: {total}"
)

print()

# ------------------------------------------------------------
# Process in batches
# ------------------------------------------------------------

for start in range(
    0,
    total,
    BATCH_SIZE
):

    end = min(
        start + BATCH_SIZE,
        total
    )

    batch = df.iloc[
        start:end
    ]

    batch_images = []

    batch_ids = []

    batch_rows = []

    # --------------------------------------------------------
    # Download batch images
    # --------------------------------------------------------

    for _, row in batch.iterrows():

        product_id = str(
            row["product_id"]
        )

        url = str(
            row["image_url"]
        )

        image = download_image(
            url,
            session
        )

        if image is None:

            status_records.append({
                "product_id":
                    product_id,
                "image_url":
                    url,
                "status":
                    "failed"
            })

            continue

        try:

            tensor = preprocess(
                image
            )

            batch_images.append(
                tensor
            )

            batch_ids.append(
                product_id
            )

            batch_rows.append(
                row
            )

        except Exception:

            status_records.append({
                "product_id":
                    product_id,
                "image_url":
                    url,
                "status":
                    "preprocess_failed"
            })

            continue

    # --------------------------------------------------------
    # Run ResNet50
    # --------------------------------------------------------

    if batch_images:

        image_tensor = torch.stack(
            batch_images
        )

        image_tensor = image_tensor.to(
            DEVICE
        )

        with torch.no_grad():

            features = model(
                image_tensor
            )

        # Shape:
        # batch x 2048 x 1 x 1

        features = features.flatten(
            start_dim=1
        )

        # Normalize embeddings
        features = torch.nn.functional.normalize(
            features,
            p=2,
            dim=1
        )

        features_np = (
            features
            .cpu()
            .numpy()
            .astype(np.float32)
        )

        embeddings.append(
            features_np
        )

        # Save successful IDs
        for product_id in batch_ids:

            successful_product_ids.append(
                product_id
            )

            status_records.append({
                "product_id":
                    product_id,
                "status":
                    "success"
            })

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    processed = end

    success_count = len(
        successful_product_ids
    )

    print(
        f"Processed "
        f"{processed}/{total} "
        f"| Successful images: "
        f"{success_count}"
    )


# ============================================================
# CLOSE SESSION
# ============================================================

session.close()


# ============================================================
# CHECK RESULTS
# ============================================================

if not embeddings:

    raise RuntimeError(
        "No images were successfully processed."
    )


# Combine all batches
final_embeddings = np.vstack(
    embeddings
)


# ============================================================
# SAVE IMAGE EMBEDDINGS
# ============================================================

print()

print(
    "Saving image embeddings..."
)

np.save(
    OUTPUT_EMBEDDINGS,
    final_embeddings
)


# ============================================================
# SAVE PRODUCT ID MAPPING
# ============================================================

image_product_ids = pd.DataFrame({
    "product_id":
        successful_product_ids
})

image_product_ids.to_csv(
    OUTPUT_PRODUCT_IDS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# SAVE STATUS
# ============================================================

status_df = pd.DataFrame(
    status_records
)

status_df.to_csv(
    OUTPUT_STATUS,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("IMAGE EMBEDDINGS COMPLETE")
print("=" * 70)

print()

print(
    "Products in original dataset:",
    len(df)
)

print()

print(
    "Successful image embeddings:",
    len(successful_product_ids)
)

print()

print(
    "Failed / skipped images:",
    len(df)
    - len(successful_product_ids)
)

print()

print(
    "Embedding shape:"
)

print(
    final_embeddings.shape
)

print()

print(
    "Expected dimension:"
)

print(
    "(number_of_successful_images, 2048)"
)

print()

print(
    "Embedding dtype:"
)

print(
    final_embeddings.dtype
)

print()

print(
    "Saved image embeddings:"
)

print(
    OUTPUT_EMBEDDINGS
)

print()

print(
    "Saved product IDs:"
)

print(
    OUTPUT_PRODUCT_IDS
)

print()

print(
    "Saved status:"
)

print(
    OUTPUT_STATUS
)

print()

print(
    "First embedding:"
)

print(
    final_embeddings[0][:10]
)

print()

print("=" * 70)
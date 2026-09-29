from pathlib import Path


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
IMAGES_DIR = DATA_DIR / "images"

METADATA_DIR = RAW_DIR / "metadata"
REVIEWS_DIR = RAW_DIR / "reviews"

# Raw dataset files
METADATA_FILE = (
    METADATA_DIR / "meta_Clothing_Shoes_and_Jewelry.jsonl.gz"
)

REVIEWS_FILE = (
    REVIEWS_DIR / "Clothing_Shoes_and_Jewelry.jsonl.gz"
)

# Project limits
MAX_PRODUCTS = 5000
MAX_REVIEWS = 50000

# Minimum useful reviews per product
MIN_REVIEWS_PER_PRODUCT = 2

# Random seed
RANDOM_SEED = 42
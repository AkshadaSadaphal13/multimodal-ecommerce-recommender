"""Product routes for the recommendation backend."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter

router = APIRouter(prefix='/products', tags=['products'])

_DATA_PATH = Path(__file__).resolve().parents[3] / 'data' / 'processed' / 'products_aligned.csv'


@router.get('/')
def list_products(limit: int = 10):
    if not _DATA_PATH.exists():
        return {'products': []}

    df = pd.read_csv(_DATA_PATH)
    return {'products': df.head(limit).to_dict(orient='records')}

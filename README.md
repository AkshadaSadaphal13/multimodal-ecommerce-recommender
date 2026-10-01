# Multimodal E-Commerce Recommendation System

## Problem

Product discovery can be difficult when shoppers do not know the exact product name. This project provides text, image, and text plus image search, with product metadata and review sentiment in recommendation results.

## Features

- Text search using Sentence-BERT and a 384D cosine FAISS index.
- Image search using ResNet50 features projected to 256D.
- Text plus image weighted query fusion against the three-modal product index.
- Category, minimum rating, and maximum price filters.
- Product image galleries with sequential URL fallback.
- Recommendation explanations, rating/review summaries, wishlist, bag, and user history/preferences endpoints.
- Evaluation data audits and a rating-proxy sentiment evaluation.

## Data

The repository contains a processed subset of Amazon Reviews 2023. `data/processed/products_aligned.csv` is the aligned product metadata table used by retrieval; review data is in `reviews_multicategory_sentiment.csv`. The working subset has approximately 2,500 products across All Beauty, Digital Music, Gift Cards, Health & Personal Care, and Video Games. Raw source data is not included.

## Models and retrieval architecture

- Product/query text: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- Product/query images: pretrained ResNet50 (2,048 dimensions), followed by the saved image projection to 256 dimensions.
- Reviews: Sentence-BERT embeddings and the existing sentiment labels/statistics.
- Text retrieval: normalized text vectors in `index/text_product_index.faiss` with `text_product_ids.csv`.
- Image retrieval: projected normalized image vectors in `index/image_product_index.faiss` with `image_product_ids.csv`.
- Three-modal product retrieval: `index/three_modal_product_index.faiss`; product-side fusion uses image 0.4, text 0.4, review 0.2.
- Text plus image query fusion normalizes its two user-provided weights and searches the three-modal product index.
- FAISS `IndexFlatIP` uses inner product on normalized vectors, equivalent to cosine similarity.

Index rows and their ID files must remain in the same order. The text index was rebuilt from the existing 2,500 text embeddings because the former index had 5,000 vectors and no matching current ID file. The image index was built from existing image embeddings and the saved projection. No model embeddings were regenerated.

## Application architecture

- FastAPI backend: `backend/app`; recommendation endpoints are under `/api`.
- React and Vite frontend: `frontend/`.
- Core feature extraction, retrieval, and ranking: `backend/app/services/retrieval_service.py`.

## Installation and running

Use Python 3.10+ and Node.js. Install the pinned Python dependencies and frontend dependencies:

```bash
python -m pip install -r requirements.txt
cd frontend
npm install
```

Start the API from the repository root:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

The backend loads pretrained model weights on startup. The first run may require locally available model weights or network access to download them. `VITE_API_URL` can override the frontend API base URL.

## API endpoints

- `GET /health`
- `POST /api/recommend` (JSON: query, top_k, category, min_rating, max_price)
- `POST /api/recommend/image` (multipart image and optional filters)
- `POST /api/recommend/multimodal` (multipart image, query, weights, and optional filters)
- `GET /api/products/`
- User preference, history, profile, and personalization routes are under `/api/users`.

Interactive API documentation is available at `/docs` while the backend is running.

## Evaluation and baselines

Run `python scripts/evaluate_recommender.py` to audit recommendation relevance data and produce `evaluation_results.csv`. The supplied `interactions.csv` uses synthetic product IDs that do not join to the catalog; reviews identify reviewed products but do not establish query-to-result relevance. Recommendation Precision@K, Recall@K, NDCG@K, and Hit Rate@K are therefore intentionally left blank for text-only, image-only, text plus image, and three-modal models. Valid baseline comparison requires held-out user interactions or relevance judgments joined to catalog products. No performance advantage is claimed.

Run `python scripts/evaluate_sentiment.py` to calculate accuracy, precision, recall, and F1 against weak labels derived from star ratings (4–5 positive, 1–2 negative, 3 excluded). These are agreement metrics against a proxy, not independently verified sentiment ground truth.

## Limitations

- The catalog is a small subset, and image URLs may be unavailable at their host.
- Personalization is content-based and relies on local user history/preferences; it is not evidence of improved engagement.
- Recommendation effectiveness cannot be quantified until valid held-out relevance data is supplied.
- The sentiment evaluation uses rating-derived proxy labels.

## Future work

- Collect or provide held-out user interactions for offline recommendation metrics and baseline comparison.
- Add explicit product detail lookup and richer review excerpts.
- Evaluate personalization with user-level train/test splits and user consented interaction data.
- Add deployment monitoring and authenticated user accounts.

# MultiRecommend — Multimodal E-Commerce Recommendation System

MultiRecommend is a product discovery and recommendation web application. Shoppers can search a product catalog with text, an uploaded image, or both together. The React storefront presents the catalog and recommendations, while a FastAPI service retrieves candidates from precomputed FAISS indexes and records optional user activity for personalization.

> This repository is a research and demonstration project. Its account UI is not production authentication, and its recommendation quality has not been established with a valid held-out relevance benchmark.

## Contents

- [Highlights](#highlights)
- [How recommendations work](#how-recommendations-work)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Run locally](#run-locally)
- [Run with Docker](#run-with-docker)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Data and model artifacts](#data-and-model-artifacts)
- [User data and privacy](#user-data-and-privacy)
- [Evaluation](#evaluation)
- [Troubleshooting](#troubleshooting)
- [Known limitations](#known-limitations)

## Highlights

- **Text search:** describe a product in natural language and retrieve matching products.
- **Image search:** upload a JPG, PNG, or WEBP image to find visually similar products.
- **Multimodal search:** combine an image and text prompt, with adjustable text and image weights.
- **Catalog browsing:** browse the processed catalog, categories, product images, ratings, and available filters.
- **Recommendation explanations:** show match information and product/review signals where available.
- **Personalization:** store product views, searches, wishlist/cart events, and category/price preferences in SQLite; use that activity for personalized recommendations.
- **Storefront features:** responsive product cards and details, wishlist, shopping bag, and profile views.
- **Image fallback:** product cards can try alternate image URLs when a source image fails to load.

The catalog currently contains approximately 2,499 aligned products across **All Beauty**, **Digital Music**, **Gift Cards**, **Health & Personal Care**, and **Video Games**. Product images are hosted externally and can become unavailable independently of this project.

## How recommendations work

1. **Text features** are encoded with `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
2. **Image features** use pretrained ResNet50 features (2,048 dimensions), then the saved image projection maps them to 256 dimensions.
3. **Review features** use Sentence-BERT embeddings and existing review sentiment/statistics where available.
4. **Precomputed, normalized product vectors** are searched using FAISS inner product. For normalized vectors, inner product is equivalent to cosine similarity.
5. Text-only, image-only, and text-plus-image searches use their corresponding FAISS indexes and aligned product-ID tables. The three-modal product index uses the existing product-side feature fusion (image 0.4, text 0.4, review 0.2). Query weights for multimodal search are normalized by the API.
6. Product metadata and review summaries are joined to search results. Personalization uses stored interactions and preferences when there is enough history; new users receive cold-start recommendations.

Index files and their corresponding ID tables must remain aligned and must not be reordered independently. The checked-in text index was rebuilt to match the available product IDs; existing embeddings were used rather than regenerating all model features.

## Architecture

```text
React + Vite storefront (frontend/)
        │ HTTP / multipart image uploads
        ▼
FastAPI API (backend/app/)
  ├── retrieval and ranking services
  ├── text, image, and multimodal routes
  ├── product catalog routes
  └── personalization / history routes ── SQLite (data/user_history.db)

FAISS indexes + aligned product IDs + projections + processed catalog
```

- **Frontend:** React 18, Vite 5, JavaScript, CSS.
- **Backend:** Python, FastAPI, Sentence Transformers, PyTorch/Torchvision, pandas, NumPy, and FAISS.
- **Persistence:** SQLite through SQLAlchemy. The database stores a generated user ID, optional profile name/email, preferences, and interaction history.
- **Retrieval implementation:** `backend/app/services/retrieval_service.py` and `backend/app/services/recommendation_service.py`.

## Repository layout

```text
backend/
  app/
    main.py                   FastAPI app, CORS, startup and router registration
    routes/                   recommendation, product, and user endpoints
    models/                   SQLAlchemy database models
    schemas/                  API request/response schemas
    services/                 retrieval, embedding, history, personalization
  tests/                      backend tests
data/
  processed/                  aligned catalog, reviews, and supporting CSVs
  embeddings/                 saved embeddings, projections, and product IDs
  images/                     available image assets
  user_history.db             local runtime database (ignored by Git)
frontend/
  src/                        React application, components, pages, styles, API client
  Dockerfile                  Vite build served by Nginx
  nginx.conf                  frontend container web-server configuration
index/                        FAISS search indexes
models/                       optional locally cached model assets
scripts/                      data preparation and evaluation scripts
Dockerfile.backend             backend container build
docker-compose.yml             frontend + backend development deployment
requirements.txt               local Python dependencies
requirements.docker.txt        Docker Python dependencies
```

## Requirements

For local development:

- Python 3.10 or later (the Docker image uses Python 3.12).
- Node.js 20 or later and npm.
- Git.
- Enough memory and disk space for PyTorch, model weights, FAISS indexes, and the processed data.

The backend initializes the retrieval service and loads its indexes and models during startup. On a first run, pretrained weights may need to be downloaded, so allow network access and time for model initialization. If weights are already cached or supplied under `models/`, they can be reused.

## Run locally

Open two terminals from the repository root.

### 1. Install backend dependencies

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, use an approved execution policy for your user or run the venv's Python executable directly.

### 2. Start the backend

From the repository root, with the virtual environment active:

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive OpenAPI docs are at `http://127.0.0.1:8000/docs`; health check is `http://127.0.0.1:8000/health`.

### 3. Install and start the frontend

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. The frontend uses `http://127.0.0.1:8000` as its default API base URL. To override it, create `frontend/.env.local`:

```dotenv
VITE_API_URL=http://127.0.0.1:8000
```

Vite reads `VITE_*` variables at startup; restart the dev server after changing them.

### Frontend build

```bash
cd frontend
npm run build
npm run preview
```

`npm run build` writes the production frontend to `frontend/dist/`.

## Run with Docker

Docker Compose builds a CPU-based FastAPI image and a production React image served by Nginx. It exposes the application at `http://localhost:5173` and the API at `http://localhost:8000`.

### Prerequisites

- Docker Desktop with Docker Compose, or Docker Engine plus the Compose plugin.
- The checked-in processed catalog, FAISS indexes, embeddings, and projections required by retrieval.
- Enough disk space to build the PyTorch/FAISS backend image and fetch any uncached pretrained model weights.

### Start the application

The SQLite database is local runtime data and is intentionally not committed. Create the bind-mounted file before the first Compose start.

PowerShell:

```powershell
New-Item -ItemType File -Force data/user_history.db
docker compose up --build
```

macOS/Linux:

```bash
mkdir -p data
touch data/user_history.db
docker compose up --build
```

Wait for backend model initialization, then open `http://localhost:5173`. The compose file builds the frontend with `VITE_API_URL=http://localhost:8000`; that URL is used by the browser on the host. The backend listens on port 8000. The database file is bind-mounted at `/app/data/user_history.db`, so local user activity persists across container restarts.

Useful commands:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose down
```

To rebuild after source or dependency changes:

```bash
docker compose up --build
```

The Compose setup mounts `data/processed`, `data/embeddings`, `index`, and `models` read-only into the backend. Keep those paths and the files within them available in the checkout. `data/user_history.db` is writable and persists on the host. Do not delete it if you want to retain local history.

### Docker configuration notes

- Backend image instructions are in `Dockerfile.backend`; frontend instructions are in `frontend/Dockerfile`.
- The backend image installs CPU-only PyTorch/Torchvision using `requirements.docker.txt`.
- The frontend image runs `npm ci`, builds with Vite, and serves `dist/` using Nginx.
- The Compose service names are `backend` and `frontend`.
- If you deploy the frontend on another host or domain, rebuild it with a `VITE_API_URL` that is reachable from the user's browser; `localhost` only points to the machine running the browser.
- For production deployment, configure CORS for the intended frontend origin and use HTTPS. The current backend CORS policy is permissive for development.

## Configuration

| Variable | Used by | Default | Purpose |
| --- | --- | --- | --- |
| `VITE_API_URL` | Vite frontend | `http://127.0.0.1:8000` locally | Base URL the browser uses for API requests. For Docker Compose, it is set to `http://localhost:8000`. |
| `DATABASE_URL` | FastAPI backend | `sqlite:///data/user_history.db` resolved from the project root | SQLAlchemy database URL. Compose sets `sqlite:////app/data/user_history.db`. |
| `HF_TOKEN` | Optional model downloads | unset | Optional Hugging Face token for gated/private model access; the public configured Sentence-BERT model normally does not require one. |

The root `.env.example` documents optional environment settings. Do not commit real tokens, credentials, or private environment files.

## API reference

Open `/docs` on a running backend for the authoritative interactive schema. Common endpoints include:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | API status and docs location. |
| `GET` | `/health` | Basic health response. |
| `POST` | `/api/recommend` | Text search. JSON fields include `query`, `top_k`, `category`, `min_rating`, and `max_price`. |
| `POST` | `/api/recommend/image` | Image search. Multipart fields include `image`, `top_k`, and optional filters. Accepts JPG, PNG, or WEBP up to 10 MB. |
| `POST` | `/api/recommend/multimodal` | Text-plus-image search. Multipart fields include `image`, `query`, `text_weight`, `image_weight`, `top_k`, and optional filters. Both weights cannot be zero. |
| `GET` | `/products/` and `/api/products/` | List catalog products; `limit` defaults to 10 and is capped at 3,000. |
| `POST` | `/api/users` | Create or update a personalization profile using optional `name`, `email`, and `user_id`. Returns the generated/linked ID. |
| `POST` | `/api/users/{user_id}/preferences` | Save category and price preferences. |
| `POST` | `/api/users/{user_id}/history` | Record a view, search, wishlist, cart, or purchase event. |
| `GET` | `/api/users/{user_id}/history` | Read a user's event history. |
| `GET` | `/api/users/{user_id}/profile` | Read profile metadata, preference summary, and history count. |
| `GET` | `/api/users/{user_id}/recommendations` | Get personalized recommendations; accepts `top_k`, `query`, and `category`. |

Example text request:

```bash
curl -X POST http://127.0.0.1:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query":"lightweight moisturizer for sensitive skin","top_k":10,"category":"All Beauty","min_rating":3.5}'
```

Image endpoints use `multipart/form-data`; use the interactive docs or the frontend for uploads.

## Data and model artifacts

- `data/processed/products_aligned.csv` is the catalog metadata file read by retrieval; related processed product and review CSV files are also included.
- `data/embeddings/` contains precomputed vectors, projection matrices, and aligned product-ID CSV files.
- `index/` contains the prebuilt FAISS indexes. Their row order must match their companion ID tables.
- `models/` can contain locally cached model files. The configured Sentence-BERT and ResNet50 weights may otherwise be loaded/downloaded by their libraries.
- Raw source data is excluded from this repository. `data/raw/` is ignored by Git.
- The SQLite database is created locally and ignored by Git. It is not sample catalog data.

The dataset is based on a processed subset of Amazon Reviews 2023. Consult the source dataset terms and attribution requirements before redistributing data or using it outside this project. Product image URLs point to third-party hosts and are not guaranteed to stay online.

## User data and privacy

- SQLite data is stored in `data/user_history.db` for local runs and bind-mounted from that path in Docker Compose.
- User IDs are generated identifiers. The current API can store the profile name/email associated with a personalization ID, as well as preferences and recommendation activity.
- The storefront's account flow is a demonstration profile flow; it does not validate passwords or implement secure authentication, password storage, session tokens, or account recovery. Do not use it to protect real accounts or sensitive information.
- Wishlist, shopping bag, and order demo state may be kept in browser local storage. This is separate from backend order/payment processing; no payment system is implemented.
- Before sharing screenshots, database files, logs, or backups, check them for personal data. The local database is excluded by `.gitignore`.

## Evaluation

Run the evaluation scripts from the repository root with the Python environment installed:

```bash
python scripts/evaluate_recommender.py
python scripts/evaluate_sentiment.py
```

`evaluate_recommender.py` audits the relevance inputs and writes `evaluation_results.csv`. The checked-in interaction data uses synthetic product IDs that do not join to the product catalog, and reviews do not supply query-to-result relevance judgments. As a result, Precision@K, Recall@K, NDCG@K, and Hit Rate@K are intentionally left blank rather than reported as meaningful model scores.

`evaluate_sentiment.py` computes agreement with weak labels derived from star ratings (4–5 positive, 1–2 negative, 3 excluded). These are proxy-label metrics, not independently verified sentiment ground truth. Existing result CSVs are outputs, not proof of production-level performance.

## Troubleshooting

### Frontend cannot reach the API

- Confirm the backend is running at `http://127.0.0.1:8000/health`.
- Check `VITE_API_URL` and restart Vite after changing `.env.local`.
- In Docker, ensure the frontend is built with the correct browser-reachable API URL. `localhost` in a browser refers to the browser's host, not an arbitrary remote container host.
- Check the browser console and backend logs for CORS or API errors.

### Backend fails during startup

- Verify required files exist: `data/processed/products_aligned.csv`, the FAISS indexes under `index/`, companion product-ID files under `data/embeddings/`, and the saved projection matrices.
- Check that each FAISS index has the same number of rows as its product-ID table.
- Allow time and network access for uncached pretrained weights, or make the expected weights available in the model cache.
- In Docker, check `docker compose logs -f backend` and confirm that the Compose mounts resolve to the repository's actual `data`, `index`, and `models` directories.

### Docker database mount errors

Create `data/user_history.db` as a file before running Compose (commands above). If Docker reports that the host path is a directory, stop the containers and inspect/fix that host path before retrying; preserve a backup if it contains data.

### Missing product images

Product image URLs are external. A URL can be invalid, blocked, or removed by its host. Cards try available alternate URLs when supplied, but the project cannot guarantee third-party image availability.

## Known limitations

- The catalog is a small subset rather than a live retail inventory.
- Gift card variants and other product variants may reuse the same source image in the input data.
- Prices, stock, and image links are catalog metadata, not live retailer data.
- Personalization is based on recorded interactions and preferences; there is no evidence here that it improves user engagement or conversion.
- Valid offline recommendation metrics require held-out interactions or relevance judgments linked to catalog product IDs.
- The email/name profile is not secure identity verification; login credentials are not authenticated by the backend.
- The backend currently allows all CORS origins for development; production deployment should restrict this.

## Contributing and Git hygiene

Before committing, review `git status` and confirm that local databases, secrets, virtual environments, downloaded raw datasets, and build outputs are not staged. Precomputed model/index artifacts are part of the current application and are not all ignored; large files may need Git LFS depending on the hosting provider's file-size limits.

## License

No project license file is currently included. Add a `LICENSE` file before redistributing this code under an explicit license. Data and third-party model assets may have separate terms.

# Multimodal E-Commerce Recommendation System

An AI-powered e-commerce recommendation system that combines
product images, product text, and customer reviews to generate
personalized product recommendations.

## Features

- Text-based product search
- Image-based product search
- Multimodal text + image search
- Product image feature extraction
- Product text embeddings
- Customer review embeddings
- Review sentiment analysis
- Multimodal weighted fusion
- FAISS similarity search
- Category filtering
- Rating filtering
- Price filtering
- Top-K recommendations
- React frontend
- FastAPI backend

## AI / ML Models

### Image
ResNet50

### Product Text
Sentence-BERT
`all-MiniLM-L6-v2`

### Reviews
Sentence-BERT

### Sentiment
DistilBERT
`distilbert-base-uncased-finetuned-sst-2-english`

### Retrieval
FAISS IndexFlatIP

## Architecture

Images → ResNet50
Product Text → Sentence-BERT
Reviews → Sentence-BERT + Sentiment
↓
Projection
↓
Weighted Multimodal Fusion
↓
FAISS
↓
Top-K Recommendations

## Technology Stack

- Python
- PyTorch
- Torchvision
- Transformers
- Sentence Transformers
- FAISS
- FastAPI
- React
- Vite
- Axios
- Pandas
- NumPy
- Scikit-learn

## Dataset

Amazon Reviews 2023.

The complete raw dataset is not included in this repository because
of its large size.

## Running the Backend

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
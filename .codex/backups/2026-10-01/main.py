from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes import users
from app.routes.recommendations import router as recommendations_router


# ---------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------

app = FastAPI(
    title="Multimodal E-Commerce Recommendation System",
    description=(
        "Multimodal e-commerce recommendation system using "
        "ResNet50, Sentence-BERT, review embeddings, FAISS, "
        "cold-start handling, and personalized recommendations."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------

@app.on_event("startup")
def startup_event():
    """
    Initialize SQLite database and create required tables.
    """
    init_db()


# ---------------------------------------------------------
# Routes
# ---------------------------------------------------------

# Existing recommendation APIs
app.include_router(
    recommendations_router
)

# User, preferences and history APIs
app.include_router(
    users.router
)


# ---------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Multimodal E-Commerce Recommendation System API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "multimodal-ecommerce-recommendation-api",
    }
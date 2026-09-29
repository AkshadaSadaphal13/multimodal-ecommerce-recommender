"""FastAPI backend entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.products import router as products_router
from .routes.recommendations import router as recommendations_router


app = FastAPI(
    title="Multimodal E-Commerce Recommender",
    description="Multimodal product recommendation system",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(products_router)
app.include_router(recommendations_router)


@app.get("/")
def read_root():
    return {
        "message": "Multimodal E-Commerce Recommender is running."
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }
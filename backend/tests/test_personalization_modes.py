import unittest
from datetime import datetime, timedelta, timezone
import sys
from types import SimpleNamespace
from types import ModuleType
from unittest.mock import patch

import numpy as np
import pandas as pd

# Unit coverage can run without the optional FAISS wheel; production calls use
# faiss.normalize_L2 and the loaded index through the same interface.
try:
    import faiss  # noqa: F401
    REAL_FAISS_AVAILABLE = True
except ImportError:
    REAL_FAISS_AVAILABLE = False
    faiss_stub = ModuleType("faiss")

    def normalize_l2(vectors):
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors /= np.where(norms == 0, 1, norms)

    faiss_stub.normalize_L2 = normalize_l2
    sys.modules["faiss"] = faiss_stub

from backend.app.services.personalization_service import PersonalizationService


class FakeFaissIndex:
    ntotal = 6

    def __init__(self):
        self.queries = []

    def search(self, query, count):
        self.queries.append(query.copy())
        indexes = np.arange(min(count, self.ntotal), dtype=np.int64)
        scores = np.linspace(0.99, 0.5, len(indexes), dtype=np.float32)
        return scores.reshape(1, -1), indexes.reshape(1, -1)


def service_fixture():
    service = object.__new__(PersonalizationService)
    service.product_ids = [f"P{index}" for index in range(1, 7)]
    service.product_id_to_index = {product_id: index for index, product_id in enumerate(service.product_ids)}
    service.embeddings = np.asarray([
        [1.0, 0.0], [0.9, 0.1], [0.8, 0.2],
        [0.0, 1.0], [0.1, 0.9], [0.2, 0.8],
    ], dtype=np.float32)
    service.index = FakeFaissIndex()
    service.products = pd.DataFrame([
        {"product_id": f"P{index}", "title": title, "main_category": category,
         "average_rating": rating, "rating_number": reviews, "price": 20 + index,
         "image_url": f"https://example.test/{index}.jpg", "images": "[]", "store": "Test"}
        for index, (title, category, rating, reviews) in enumerate([
            ("Moisturizer alpha", "Beauty", 4.9, 500),
            ("Moisturizer beta", "Beauty", 4.7, 400),
            ("Face cream", "Beauty", 4.6, 300),
            ("Game controller", "Video Games", 4.8, 1000),
            ("Beauty lotion", "Beauty", 4.5, 200),
            ("Gift card", "Gift Cards", 5.0, 50),
        ], start=1)
    ])
    service.products["combined_text"] = service.products["title"]
    service.product_lookup = service.products.set_index("product_id", drop=False).to_dict(orient="index")
    return service


class PersonalizationModeTests(unittest.TestCase):
    def test_empty_history_uses_cold_start_and_current_context(self):
        service = service_fixture()
        with patch("backend.app.services.personalization_service.get_user_interactions", return_value=[]), \
             patch.object(service, "get_user_preferences", return_value={"categories": [], "min_price": 0, "max_price": None}):
            result = service.get_personalized_recommendations(
                db=None, user_id="new-user", top_k=5,
                context_query="moisturizer", context_category="Beauty",
            )

        self.assertTrue(result["cold_start"])
        self.assertEqual(result["mode"], "cold_start")
        self.assertFalse(result["profile"]["personalized"])
        self.assertTrue(result["recommendations"])
        self.assertTrue(all(item["category"] == "Beauty" for item in result["recommendations"]))
        self.assertTrue(all(item["cold_start_reason"] == "query_and_category" for item in result["recommendations"]))
        self.assertNotIn("personalized_score", result["recommendations"][0])
        self.assertEqual(service.index.queries, [])

    def test_returning_user_uses_vector_and_faiss_after_three_distinct_products(self):
        service = service_fixture()
        now = datetime.now(timezone.utc)
        interactions = [
            SimpleNamespace(product_id=f"P{index}", event_type=event, timestamp=now + timedelta(seconds=index))
            for index, event in enumerate(("view", "wishlist", "cart"), start=1)
        ]
        with patch("backend.app.services.personalization_service.get_user_interactions", return_value=interactions), \
             patch.object(service, "get_user_preferences", return_value={"categories": [], "min_price": 0, "max_price": None}):
            result = service.get_personalized_recommendations(db=None, user_id="returning-user", top_k=2)

        self.assertFalse(result["cold_start"])
        self.assertEqual(result["mode"], "history_based")
        self.assertEqual(result["profile"]["distinct_product_count"], 3)
        self.assertTrue(result["recommendations"])
        self.assertTrue(all(item["product_id"] not in {"P1", "P2", "P3"} for item in result["recommendations"]))
        self.assertTrue(all("similarity" in item for item in result["recommendations"]))
        self.assertTrue(result["based_on_interests"])
        expected = np.asarray([6.9, 1.1], dtype=np.float32)
        expected /= np.linalg.norm(expected)
        self.assertTrue(np.allclose(service.index.queries[-1][0], expected, atol=1e-5))


@unittest.skipUnless(REAL_FAISS_AVAILABLE, "faiss-cpu is not installed")
class RealFaissPersonalizationIntegrationTests(unittest.TestCase):
    def test_empty_then_returning_history_against_project_index(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from backend.app.database import Base
        from backend.app.models.user import User, UserHistory

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        service = PersonalizationService()
        with Session(engine) as db:
            db.add(User(user_id="integration-user"))
            db.commit()

            empty = service.get_personalized_recommendations(db, "integration-user", top_k=5)
            self.assertEqual(empty["mode"], "cold_start")
            self.assertTrue(empty["recommendations"])

            for product_id, event_type in zip(service.product_ids[:3], ("view", "wishlist", "cart")):
                db.add(UserHistory(user_id="integration-user", product_id=product_id, event_type=event_type))
            db.commit()

            returning = service.get_personalized_recommendations(db, "integration-user", top_k=5)
            self.assertEqual(returning["mode"], "history_based")
            self.assertEqual(returning["profile"]["distinct_product_count"], 3)
            self.assertTrue(returning["recommendations"])
            self.assertTrue(all("similarity" in item for item in returning["recommendations"]))
        engine.dispose()


class UserHistoryApiTests(unittest.TestCase):
    def test_event_sync_is_idempotent(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from sqlalchemy.pool import StaticPool

        from backend.app.database import Base, get_db
        from backend.app.routes.users import router

        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=engine)
        test_sessions = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        app = FastAPI()
        app.include_router(router)

        def override_get_db():
            session = test_sessions()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as client:
            user_response = client.post("/api/users", json={})
            self.assertEqual(user_response.status_code, 200)
            user_id = user_response.json()["user_id"]
            event = {"event_id": "local-event-1", "product_id": "__search__", "event_type": "search", "query": "running shoes"}

            first = client.post(f"/api/users/{user_id}/history", json=event)
            duplicate = client.post(f"/api/users/{user_id}/history", json=event)
            history = client.get(f"/api/users/{user_id}/history")

            self.assertEqual(first.status_code, 200)
            self.assertEqual(duplicate.status_code, 200)
            self.assertEqual(first.json()["id"], duplicate.json()["id"])
            self.assertEqual(len(history.json()), 1)
            self.assertEqual(history.json()[0]["query"], "running shoes")
        engine.dispose()


if __name__ == "__main__":
    unittest.main()

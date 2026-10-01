from sqlalchemy.orm import Session

from app.models.user import UserHistory


EVENT_WEIGHTS = {
    "view": 1.0,
    "search": 2.0,
    "wishlist": 3.0,
    "cart": 4.0,
    "purchase": 5.0,
}


def save_history_event(
    db: Session,
    user_id: str,
    product_id: str,
    event_type: str,
    query: str | None = None,
):
    history = UserHistory(
        user_id=user_id,
        product_id=product_id,
        event_type=event_type,
        query=query,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history


def get_user_history(
    db: Session,
    user_id: str,
):
    return (
        db.query(UserHistory)
        .filter(UserHistory.user_id == user_id)
        .order_by(UserHistory.timestamp.desc())
        .all()
    )


def get_user_interactions(
    db: Session,
    user_id: str,
):
    return (
        db.query(UserHistory)
        .filter(UserHistory.user_id == user_id)
        .all()
    )


def get_event_weight(event_type: str) -> float:
    return EVENT_WEIGHTS.get(event_type, 1.0)


def get_history_count(
    db: Session,
    user_id: str,
) -> int:
    return (
        db.query(UserHistory)
        .filter(UserHistory.user_id == user_id)
        .count()
    )


def is_cold_start(
    db: Session,
    user_id: str,
) -> bool:
    return get_history_count(db, user_id) == 0
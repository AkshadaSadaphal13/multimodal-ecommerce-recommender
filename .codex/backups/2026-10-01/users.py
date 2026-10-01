from app.services.personalization_service import (
    PersonalizationService
)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserPreference, UserHistory
from app.schemas.user import (
    UserCreate,
    UserResponse,
    PreferenceCreate,
    PreferenceResponse,
    HistoryCreate,
    HistoryResponse,
)

router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


ALLOWED_EVENTS = {
    "view",
    "search",
    "wishlist",
    "cart",
    "purchase",
}


@router.post(
    "",
    response_model=UserResponse
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    user = User()

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/{user_id}/preferences",
    response_model=PreferenceResponse
)
def save_preferences(
    user_id: str,
    preferences: PreferenceCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Remove old preferences
    db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).delete()

    categories = preferences.categories

    for category in categories:
        preference = UserPreference(
            user_id=user_id,
            category=category,
            min_price=preferences.min_price,
            max_price=preferences.max_price,
        )

        db.add(preference)

    user.is_new_user = False

    db.commit()

    return PreferenceResponse(
        user_id=user_id,
        categories=categories,
        min_price=preferences.min_price,
        max_price=preferences.max_price,
    )


@router.post(
    "/{user_id}/history",
    response_model=HistoryResponse
)
def add_history(
    user_id: str,
    history_data: HistoryCreate,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if history_data.event_type not in ALLOWED_EVENTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Allowed: {sorted(ALLOWED_EVENTS)}"
        )

    history = UserHistory(
        user_id=user_id,
        product_id=history_data.product_id,
        event_type=history_data.event_type,
        query=history_data.query,
    )

    db.add(history)

    user.is_new_user = False

    db.commit()
    db.refresh(history)

    return history


@router.get(
    "/{user_id}/history",
    response_model=list[HistoryResponse]
)
def get_history(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    history = (
        db.query(UserHistory)
        .filter(UserHistory.user_id == user_id)
        .order_by(UserHistory.timestamp.desc())
        .all()
    )

    return history


@router.get(
    "/{user_id}/profile"
)
def get_profile(
    user_id: str,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    preferences = (
        db.query(UserPreference)
        .filter(UserPreference.user_id == user_id)
        .all()
    )

    history_count = (
        db.query(UserHistory)
        .filter(UserHistory.user_id == user_id)
        .count()
    )

    categories = list(
        dict.fromkeys(
            preference.category
            for preference in preferences
        )
    )

    min_price = (
        preferences[0].min_price
        if preferences
        else 0.0
    )

    max_price = (
        preferences[0].max_price
        if preferences
        else None
    )

    return {
        "user_id": user.user_id,
        "created_at": user.created_at,
        "is_new_user": user.is_new_user,
        "history_count": history_count,
        "categories": categories,
        "min_price": min_price,
        "max_price": max_price,
    }

@router.get(
    "/{user_id}/recommendations"
)
def get_personalized_recommendations(
    user_id: str,
    top_k: int = 10,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    top_k = max(
        1,
        min(top_k, 50)
    )

    personalization_service = (
        PersonalizationService()
    )

    result = (
        personalization_service
        .get_personalized_recommendations(
            db=db,
            user_id=user_id,
            top_k=top_k,
        )
    )

    return result
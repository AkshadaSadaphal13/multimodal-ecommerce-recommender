from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    pass


class UserResponse(BaseModel):
    user_id: str
    created_at: datetime
    is_new_user: bool

    model_config = ConfigDict(from_attributes=True)


class PreferenceCreate(BaseModel):
    categories: list[str] = Field(default_factory=list)
    min_price: float = Field(default=0.0, ge=0)
    max_price: float | None = Field(default=None, ge=0)


class PreferenceResponse(BaseModel):
    user_id: str
    categories: list[str]
    min_price: float
    max_price: float | None


class HistoryCreate(BaseModel):
    product_id: str
    event_type: str
    event_id: str | None = None
    query: str | None = None


class HistoryResponse(BaseModel):
    id: int
    user_id: str
    product_id: str
    event_type: str
    event_id: str | None = None
    query: str | None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

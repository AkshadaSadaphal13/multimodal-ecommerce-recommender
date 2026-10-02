from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    user_id: str | None = Field(default=None, min_length=1, max_length=100)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, min_length=3, max_length=255)


class UserResponse(BaseModel):
    user_id: str
    name: str | None = None
    email: str | None = None
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

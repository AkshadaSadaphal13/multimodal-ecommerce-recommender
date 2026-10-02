from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
        default=lambda: f"user_{uuid4().hex[:12]}"
    )

    name: Mapped[str | None] = mapped_column(String(120), nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    is_new_user: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    preferences = relationship(
        "UserPreference",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    history = relationship(
        "UserHistory",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    category: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    min_price: Mapped[float] = mapped_column(
        Float,
        default=0.0
    )

    max_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="preferences"
    )


class UserHistory(Base):
    __tablename__ = "user_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("users.user_id"),
        nullable=False,
        index=True
    )

    product_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    event_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    query: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )

    user = relationship(
        "User",
        back_populates="history"
    )

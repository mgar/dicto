from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
    daily_new_limit: Mapped[int | None] = mapped_column(nullable=True)
    content_preference: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'both', 'grammar', 'vocab'
    selected_levels: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated: 'A1,A2,B1'
    last_items_added_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)  # Last time auto-add added items
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

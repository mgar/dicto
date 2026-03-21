from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class VocabItem(Base):
    __tablename__ = "vocab_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10), index=True)
    word: Mapped[str] = mapped_column(String(255), index=True)
    translation: Mapped[str] = mapped_column(String(255))
    part_of_speech: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    example_sentence: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    example_translation: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

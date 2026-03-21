from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grammar_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("grammar_points.id", ondelete="CASCADE"), index=True, nullable=True
    )
    vocab_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("vocab_items.id", ondelete="CASCADE"), index=True, nullable=True
    )
    kind: Mapped[str] = mapped_column(String(16), default="grammar")  # 'grammar' or 'vocab'
    sentence: Mapped[str] = mapped_column(String(1024))
    notes: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

    grammar_point = relationship("GrammarPoint")
    vocab_item = relationship("VocabItem")
    answers = relationship("PromptAnswer", back_populates="prompt", cascade="all, delete-orphan")


class PromptAnswer(Base):
    __tablename__ = "prompt_answers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), index=True)
    answer: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

    prompt = relationship("Prompt", back_populates="answers")

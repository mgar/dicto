from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ReviewState(Base):
    __tablename__ = "review_state"
    __table_args__ = (
        Index("ix_review_state_user_status_due", "user_id", "status", "due_at"),
        Index("ix_review_state_user_introduced_local_date", "user_id", "introduced_local_date"),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True)

    ease_factor: Mapped[float]
    interval_days: Mapped[int]
    repetitions: Mapped[int]
    due_at: Mapped[object] = mapped_column(DateTime)
    last_reviewed_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    introduced_at: Mapped[object | None] = mapped_column(DateTime, nullable=True)
    introduced_local_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="reviewing")

    prompt = relationship("Prompt")
    user = relationship("User")


class ReviewLog(Base):
    __tablename__ = "review_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), index=True)

    answered_at: Mapped[object] = mapped_column(DateTime)
    local_date: Mapped[object | None] = mapped_column(Date, nullable=True, index=True)  # User's local date for activity tracking
    user_answer: Mapped[str] = mapped_column(String(255))
    grade: Mapped[int]
    is_correct: Mapped[bool]
    missing_accent: Mapped[bool] = mapped_column(default=False)
    spacing_normalized: Mapped[bool] = mapped_column(default=False)
    expected_answer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    prompt = relationship("Prompt")
    user = relationship("User")

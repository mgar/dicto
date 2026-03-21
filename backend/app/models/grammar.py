from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class GrammarPoint(Base):
    __tablename__ = "grammar_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    level: Mapped[str] = mapped_column(String(10), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    short_description: Mapped[str] = mapped_column(String(512))
    structure: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of structure patterns
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

    examples = relationship("GrammarExample", back_populates="grammar_point", cascade="all, delete-orphan")


class GrammarExample(Base):
    __tablename__ = "grammar_examples"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grammar_point_id: Mapped[int] = mapped_column(ForeignKey("grammar_points.id", ondelete="CASCADE"), index=True)
    sentence: Mapped[str] = mapped_column(String(1024))
    translation: Mapped[str] = mapped_column(String(1024))
    highlight: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

    grammar_point = relationship("GrammarPoint", back_populates="examples")

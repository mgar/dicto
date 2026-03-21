from pydantic import BaseModel


class GrammarExampleIn(BaseModel):
    sentence: str
    translation: str
    highlight: str | None = None
    notes: str | None = None
    sort_order: int = 0


class GrammarPointIn(BaseModel):
    level: str
    slug: str
    title: str
    short_description: str
    structure: list[str] | None = None  # Patterns like ["Noun + ser"]
    explanation: str
    examples: list[GrammarExampleIn] = []


class VocabItemIn(BaseModel):
    level: str
    word: str
    translation: str
    part_of_speech: str | None = None
    gender: str | None = None
    example_sentence: str | None = None
    example_translation: str | None = None
    notes: str | None = None
    tags: str | None = None  # comma-separated


class PromptIn(BaseModel):
    grammar_point_id: int | None = None
    vocab_item_id: int | None = None
    kind: str = "grammar"  # 'grammar' or 'vocab'
    sentence: str  # must contain ___ for the cloze blank
    notes: str | None = None
    answers: list[str]  # at least one required

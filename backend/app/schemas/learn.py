from pydantic import BaseModel


class LearnNextOut(BaseModel):
    added: list[dict]
    remaining: int


class PreferencesIn(BaseModel):
    daily_new_limit: int
    content_preference: str  # 'both', 'grammar', 'vocab'
    selected_levels: list[str]

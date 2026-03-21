from pydantic import BaseModel


class SubmitAnswerIn(BaseModel):
    user_answer: str
    local_date: str | None = None  # User's local date (ISO format) for timezone-aware scheduling
    tz_offset: int | None = None  # JS getTimezoneOffset(): minutes *behind* UTC (e.g. -60 for CET/UTC+1)

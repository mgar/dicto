"""
Utility functions for grading and spaced repetition.
"""
import unicodedata

from .models import GrammarPoint, Prompt, VocabItem


# -----------------------
# Mastery tiers
# -----------------------
MASTERY_TIER_LABELS = {
    "foundations": "Foundations",
    "builder": "Builder",
    "communicator": "Communicator",
    "fluent": "Fluent",
    "mastery": "Mastery",
}

MASTERY_TIER_ORDER = [
    "foundations",
    "builder",
    "communicator",
    "fluent",
    "mastery",
]


def mastery_key_from_interval(interval_days: float) -> str:
    """Map interval days to a mastery tier key."""
    if interval_days <= 2:
        return "foundations"
    if interval_days <= 7:
        return "builder"
    if interval_days <= 21:
        return "communicator"
    if interval_days <= 59:
        return "fluent"
    return "mastery"


def mastery_summary(
    total_prompts: int,
    reviewed_prompts: int,
    avg_interval_days: float | None,
    due_now: int = 0,
) -> dict:
    """Build a consistent mastery summary payload for a grammar/vocab item."""
    if total_prompts <= 0:
        return {
            "key": None,
            "label": "No prompts",
            "avg_interval_days": 0.0,
            "total_prompts": 0,
            "reviewed_prompts": 0,
            "reviewed_ratio": 0.0,
            "due_now": 0,
        }

    avg_value = float(avg_interval_days or 0.0)
    key = mastery_key_from_interval(avg_value)
    return {
        "key": key,
        "label": MASTERY_TIER_LABELS[key],
        "avg_interval_days": round(avg_value, 2),
        "total_prompts": int(total_prompts),
        "reviewed_prompts": int(reviewed_prompts),
        "reviewed_ratio": round((float(reviewed_prompts) / float(total_prompts)) * 100.0, 1),
        "due_now": int(due_now),
    }


# -----------------------
# Prompt helpers
# -----------------------
def prompt_to_dict(prompt: Prompt, grammar_point: GrammarPoint | None, vocab_item: VocabItem | None) -> dict:
    """Convert a prompt with its related grammar/vocab to a dict."""
    result = {
        "prompt_id": prompt.id,
        "kind": prompt.kind,
        "sentence": prompt.sentence,
        "notes": prompt.notes,  # Instruction hint (e.g., "Translate: coffee")
    }
    if prompt.kind == "grammar" and grammar_point:
        result["grammar_point_id"] = grammar_point.id
        result["grammar_title"] = grammar_point.title
    elif prompt.kind == "vocab" and vocab_item:
        result["vocab_item_id"] = vocab_item.id
        result["vocab_word"] = vocab_item.word
        result["vocab_translation"] = vocab_item.translation
        result["vocab_pos"] = vocab_item.part_of_speech
        result["vocab_gender"] = vocab_item.gender
        result["vocab_level"] = vocab_item.level
    return result


# -----------------------
# Cloze grading utilities
# -----------------------
def normalize_basic(text: str) -> tuple[str, bool]:
    """Normalize whitespace and case."""
    raw = text
    text = text.strip().lower()
    collapsed = " ".join(text.split())
    spacing_normalized = collapsed != text
    return collapsed, spacing_normalized or (raw != raw.strip())


def strip_accents(text: str) -> str:
    """Remove acute accent marks while preserving letters such as ñ."""
    return "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if character != "\N{COMBINING ACUTE ACCENT}"
    )


def grade_cloze(user_answer: str, accepted: list[str]) -> tuple[bool, int, dict, str | None]:
    """
    Grade a cloze answer against accepted answers.
    
    Returns:
        - is_correct: bool
        - grade: int (SM-2 grade 0-5)
        - flags: dict with missing_accent and spacing_normalized
        - expected: the canonical expected answer
    """
    user_norm, spacing = normalize_basic(user_answer)
    accepted_norm = [normalize_basic(candidate)[0] for candidate in accepted]
    accepted_noacc = [strip_accents(candidate) for candidate in accepted_norm]

    # Exact match
    if user_norm in accepted_norm:
        exact_index = accepted_norm.index(user_norm)
        user_noacc = accepted_noacc[exact_index]
        accented_match_index = next(
            (
                index
                for index, candidate in enumerate(accepted_norm)
                if index != exact_index
                and accepted_noacc[index] == user_noacc
                and candidate != strip_accents(candidate)
            ),
            None,
        )
        if accented_match_index is not None and user_norm == strip_accents(user_norm):
            return (
                True,
                3,
                {"missing_accent": True, "spacing_normalized": spacing},
                accepted_norm[accented_match_index],
            )
        return True, 4, {"missing_accent": False, "spacing_normalized": spacing}, accepted_norm[0]

    # Match without accents
    user_noacc = strip_accents(user_norm)
    if user_noacc in accepted_noacc:
        return (
            True,
            3,
            {"missing_accent": True, "spacing_normalized": spacing},
            accepted_norm[accepted_noacc.index(user_noacc)],
        )

    # Incorrect
    return (
        False,
        2,
        {"missing_accent": False, "spacing_normalized": spacing},
        accepted_norm[0] if accepted_norm else None,
    )


# -----------------------
# SM-2 scheduling algorithm
# -----------------------
def sm2_update(ease_factor: float, interval_days: int, repetitions: int, grade: int) -> tuple[float, int, int]:
    """
    Calculate new scheduling parameters using SM-2 algorithm.
    
    Args:
        ease_factor: Current ease factor (≥1.3)
        interval_days: Current interval in days
        repetitions: Number of successful repetitions
        grade: Quality grade (0-5)
    
    Returns:
        - new ease factor
        - new interval in days
        - new repetition count
    """
    working_ease = ease_factor
    working_reps = repetitions
    working_interval = interval_days

    if grade < 3:
        # Failed - reset
        working_reps = 0
        working_interval = 1
    else:
        # Success
        if working_reps == 0:
            working_interval = 1
        elif working_reps == 1:
            working_interval = 6
        else:
            working_interval = max(1, int(round(working_interval * working_ease)))
        working_reps += 1

    # Update ease factor
    working_ease = working_ease + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if working_ease < 1.3:
        working_ease = 1.3

    return working_ease, working_interval, working_reps

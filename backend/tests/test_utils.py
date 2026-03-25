"""
Tests for grade_cloze() and sm2_update() in utils.py.
These are pure functions — no DB or HTTP required.
"""
import pytest
from app.utils import grade_cloze, sm2_update


# ============================================================
# grade_cloze
# ============================================================

class TestGradeCloze:
    def test_exact_match(self):
        correct, grade, flags, expected = grade_cloze("es", ["es"])
        assert correct is True
        assert grade == 4
        assert flags["missing_accent"] is False

    def test_case_insensitive(self):
        correct, grade, flags, _ = grade_cloze("ES", ["es"])
        assert correct is True

    def test_extra_whitespace_is_normalized(self):
        correct, grade, flags, _ = grade_cloze("  es  ", ["es"])
        assert correct is True
        assert flags["spacing_normalized"] is True

    def test_internal_extra_space_normalized(self):
        correct, grade, flags, _ = grade_cloze("está  bien", ["está bien"])
        assert correct is True
        assert flags["spacing_normalized"] is True

    def test_missing_accent_accepted(self):
        correct, grade, flags, _ = grade_cloze("esta", ["está"])
        assert correct is True
        assert flags["missing_accent"] is True
        assert grade == 4

    def test_missing_accent_on_multiple_accepted(self):
        correct, grade, flags, _ = grade_cloze("comio", ["comió", "comio"])
        assert correct is True

    def test_wrong_answer(self):
        correct, grade, flags, expected = grade_cloze("son", ["es"])
        assert correct is False
        assert grade == 2
        assert expected == "es"

    def test_multiple_accepted_answers_first_matches(self):
        correct, _, _, expected = grade_cloze("está", ["está", "es"])
        assert correct is True
        assert expected == "está"

    def test_multiple_accepted_answers_second_matches(self):
        correct, _, _, _ = grade_cloze("es", ["está", "es"])
        assert correct is True

    def test_empty_accepted_list(self):
        correct, grade, flags, expected = grade_cloze("es", [])
        assert correct is False
        assert expected is None

    def test_wrong_answer_returns_first_expected(self):
        _, _, _, expected = grade_cloze("wrong", ["correcto", "otro"])
        assert expected == "correcto"


# ============================================================
# sm2_update
# ============================================================

class TestSm2Update:
    # Starting values used throughout
    DEFAULT_EF = 2.5
    DEFAULT_INTERVAL = 1
    DEFAULT_REPS = 0

    def test_first_correct_interval_is_1(self):
        ef, interval, reps = sm2_update(self.DEFAULT_EF, self.DEFAULT_INTERVAL, 0, grade=4)
        assert interval == 1
        assert reps == 1

    def test_second_correct_interval_is_6(self):
        ef, interval, reps = sm2_update(self.DEFAULT_EF, 1, 1, grade=4)
        assert interval == 6
        assert reps == 2

    def test_third_correct_uses_ef_multiplier(self):
        ease_factor, interval, reps = sm2_update(self.DEFAULT_EF, 6, 2, grade=4)
        assert interval == max(1, round(6 * self.DEFAULT_EF))
        assert reps == 3

    def test_failed_answer_resets(self):
        ease_factor, interval, reps = sm2_update(self.DEFAULT_EF, 10, 5, grade=2)
        assert reps == 0
        assert interval == 1

    def test_ef_increases_on_easy_answer(self):
        ease_factor, _, _ = sm2_update(2.5, 1, 0, grade=5)
        assert ease_factor > 2.5

    def test_ef_decreases_on_hard_answer(self):
        ease_factor, _, _ = sm2_update(2.5, 1, 0, grade=3)
        assert ease_factor < 2.5

    def test_ef_never_goes_below_1_3(self):
        # Repeatedly fail to drive EF down
        ease_factor = 2.5
        for _ in range(20):
            ease_factor, _, _ = sm2_update(ease_factor, 1, 0, grade=0)
        assert ease_factor >= 1.3

    def test_grade_3_is_passing(self):
        _, _, reps = sm2_update(2.5, 1, 1, grade=3)
        assert reps == 2  # not reset

    def test_grade_2_is_failing(self):
        _, _, reps = sm2_update(2.5, 6, 5, grade=2)
        assert reps == 0  # reset

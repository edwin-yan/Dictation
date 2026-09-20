import pytest
from app.services.grading import normalize_spelling, grade_spelling, grade_test_submission


class TestForgivingGrading:
    """Comprehensive test suite for forgiving spelling grading logic."""

    def test_exact_match(self):
        assert grade_spelling("about", "about") is True
        assert grade_spelling("school", "school") is True

    def test_case_insensitivity(self):
        assert grade_spelling("About", "about") is True
        assert grade_spelling("ABOUT", "about") is True
        assert grade_spelling("sChOoL", "school") is True
        assert grade_spelling("they're", "THEY'RE") is True

    def test_leading_and_trailing_whitespace(self):
        assert grade_spelling("  about  ", "about") is True
        assert grade_spelling("\t\nschool \n", "school") is True
        assert grade_spelling("   every   ", "  every  ") is True

    def test_smart_and_curly_apostrophes(self):
        # Tablet keyboards often output smart apostrophes (’)
        assert grade_spelling("didn’t", "didn't") is True
        assert grade_spelling("it’s", "it's") is True
        assert grade_spelling("they’re", "they're") is True
        assert grade_spelling("we’re", "we're") is True
        assert grade_spelling("you’re", "you're") is True
        assert grade_spelling("didn`t", "didn't") is True

    def test_multi_word_internal_spacing(self):
        # E.g. "a lot"
        assert grade_spelling("a lot", "a lot") is True
        assert grade_spelling("a   lot", "a lot") is True
        assert grade_spelling("  A   Lot  ", "a lot") is True

    def test_incorrect_spellings(self):
        assert grade_spelling("definatly", "definitely") is False
        assert grade_spelling("beleive", "believe") is False
        assert grade_spelling("there", "their") is False
        assert grade_spelling("hear", "here") is False
        assert grade_spelling("two", "to") is False
        assert grade_spelling("skool", "school") is False

    def test_empty_or_none_inputs(self):
        assert grade_spelling("", "about") is False
        assert grade_spelling("   ", "about") is False
        assert grade_spelling(None, "about") is False
        assert grade_spelling("about", "") is False

    def test_single_word_accidental_space_stripping(self):
        # Accidental space entered by a kid on a single word should be forgiven
        assert grade_spelling("acc ident", "accident") is True
        assert grade_spelling("s chool", "school") is True
        assert grade_spelling("be cause", "because") is True
        assert grade_spelling("  acc  ident  ", "accident", allow_multiple_words=False) is True
        # macOS / iOS double-space dot replacement or trailing period
        assert grade_spelling("acc.ident", "accident") is True
        assert grade_spelling("accident.", "accident") is True
        assert grade_spelling("acc. ident", "accident") is True
        assert grade_spelling("accident. ", "accident") is True

    def test_allow_multiple_words_flag(self):
        # When allow_multiple_words is True, words with spaces require spaces
        assert grade_spelling("a lot", "a lot", allow_multiple_words=True) is True
        assert grade_spelling("a   lot", "a lot", allow_multiple_words=True) is True
        assert grade_spelling("alot", "a lot", allow_multiple_words=True) is False

        # When allow_multiple_words is False, spaces are stripped
        assert grade_spelling("a lot", "alot", allow_multiple_words=False) is True
        assert grade_spelling("ice cream", "icecream", allow_multiple_words=False) is True

    def test_batch_grade_submission(self):
        submission = [
            {"word": "about", "student_input": "  About  ", "context_sentence": "Story about lions."},
            {"word": "didn't", "student_input": "didn’t", "context_sentence": "He didn't go."},
            {"word": "their", "student_input": "there", "context_sentence": "Their car."},
            {"word": "a lot", "student_input": "a   lot", "context_sentence": "A lot of stars."},
            {"word": "accident", "student_input": "acc ident", "context_sentence": "Accidental space."}
        ]

        result = grade_test_submission(submission)
        assert result['total'] == 5
        assert result['score'] == 4
        assert result['percentage'] == 80.0
        assert result['results'][0]['is_correct'] is True
        assert result['results'][1]['is_correct'] is True
        assert result['results'][2]['is_correct'] is False
        assert result['results'][3]['is_correct'] is True
        assert result['results'][4]['is_correct'] is True

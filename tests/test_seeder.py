import pytest
import os
from app.services.seeder import parse_pdf_lists, seed_database
from app.models import db, Student, WordList, Word, ChallengeAttempt


class TestSeeder:
    """Test PDF extraction and database seeding."""

    def test_parse_pdf_lists(self):
        pdf_path = "4th Grade Non-negotiation List.pdf"
        data = parse_pdf_lists(pdf_path)
        assert "List 1" in data
        assert "List 2" in data
        assert "List 3" in data

        list1_words = data["List 1"]["words"]
        assert "about" in list1_words
        assert "addition" in list1_words
        assert "a lot" in list1_words

        list2_words = data["List 2"]["words"]
        assert "every" in list2_words
        assert "example" in list2_words

        list3_words = data["List 3"]["words"]
        assert "school" in list3_words

    def test_seed_database(self, app):
        with app.app_context():
            seed_database(app=app, force=True)

            assert Student.query.count() >= 4
            assert WordList.query.count() >= 3
            assert Word.query.count() > 60

            # Verify List 1 has context sentences
            list1 = WordList.query.filter(WordList.title.like("%List 1%")).first()
            assert list1 is not None
            assert list1.words.count() > 0

            # Verify mock history for Alex Carter
            alex = Student.query.filter_by(name="Alex Carter").first()
            assert alex is not None
            assert alex.attempts.count() > 0
            assert alex.missed_words.count() > 0

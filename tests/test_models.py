import pytest
from app.models import db, Student, WordListFolder, WordList, Word, ChallengeAttempt, ChallengeDetail, MissedWord


class TestModels:
    """Test model integrity and relationships."""

    def test_folder_and_list_relationship(self, app):
        with app.app_context():
            folder = WordListFolder(name="4th Grade", icon="📘")
            db.session.add(folder)
            db.session.flush()

            l1 = WordList(folder_id=folder.id, title="List 1")
            l2 = WordList(folder_id=folder.id, title="List 2")
            db.session.add_all([l1, l2])
            db.session.commit()

            fetched_folder = WordListFolder.query.filter_by(name="4th Grade").first()
            assert fetched_folder is not None
            assert fetched_folder.lists.count() == 2
            assert l1.folder.name == "4th Grade"

    def test_student_and_list_association(self, app):
        with app.app_context():
            student = Student(name="Maya", avatar="🎨")
            wlist1 = WordList(title="List 1", description="Description 1")
            wlist2 = WordList(title="List 2", description="Description 2")

            db.session.add_all([student, wlist1, wlist2])
            db.session.flush()

            student.lists.append(wlist1)
            student.lists.append(wlist2)
            db.session.commit()

            fetched_student = Student.query.filter_by(name="Maya").first()
            assert fetched_student is not None
            assert fetched_student.lists.count() == 2
            assert wlist1 in fetched_student.lists
            assert wlist2 in fetched_student.lists

    def test_word_list_cascades_words(self, app):
        with app.app_context():
            wlist = WordList(title="Cascade List")
            db.session.add(wlist)
            db.session.flush()

            w1 = Word(list_id=wlist.id, word="apple", position=0)
            w2 = Word(list_id=wlist.id, word="banana", position=1)
            db.session.add_all([w1, w2])
            db.session.commit()

            assert Word.query.filter_by(list_id=wlist.id).count() == 2

            # Deleting list should cascade delete words
            db.session.delete(wlist)
            db.session.commit()

            assert Word.query.filter_by(list_id=wlist.id).count() == 0

    def test_challenge_attempt_and_details(self, app):
        with app.app_context():
            student = Student(name="Lucas", avatar="🦁")
            db.session.add(student)
            db.session.flush()

            attempt = ChallengeAttempt(
                student_id=student.id,
                title="Practice Session",
                score=2,
                total_words=3,
                percentage=66.7
            )
            db.session.add(attempt)
            db.session.flush()

            d1 = ChallengeDetail(attempt_id=attempt.id, word="cat", student_input="cat", is_correct=True)
            d2 = ChallengeDetail(attempt_id=attempt.id, word="dog", student_input="dog", is_correct=True)
            d3 = ChallengeDetail(attempt_id=attempt.id, word="fish", student_input="fsh", is_correct=False)
            db.session.add_all([d1, d2, d3])
            db.session.commit()

            fetched = db.session.get(ChallengeAttempt, attempt.id)
            assert fetched.details.count() == 3
            assert fetched.score == 2
            assert fetched.percentage == 66.7

    def test_missed_word_tracking(self, app):
        with app.app_context():
            student = Student(name="Sam", avatar="🐼")
            db.session.add(student)
            db.session.flush()

            mw = MissedWord(
                student_id=student.id,
                word="definitely",
                context_sentence="We definitely will win.",
                mistake_count=2,
                is_resolved=False
            )
            db.session.add(mw)
            db.session.commit()

            fetched_mw = MissedWord.query.filter_by(student_id=student.id, word="definitely").first()
            assert fetched_mw is not None
            assert fetched_mw.mistake_count == 2
            assert fetched_mw.is_resolved is False

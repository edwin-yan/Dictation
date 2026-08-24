import pytest
import os
from app import create_app
from app.config import Config
from app.models import db, Student, WordList, Word


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test-secret-key'
    ADMIN_PASSWORD = 'testadminpassword'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def sample_data(app):
    with app.app_context():
        # Create student
        student = Student(name="Test Kid", avatar="🚀")

        # Create list with words
        wlist = WordList(title="Test List", description="Sample testing words", category="Practice")
        db.session.add(wlist)
        db.session.flush()

        w1 = Word(list_id=wlist.id, word="about", context_sentence="A book about stars.", position=0)
        w2 = Word(list_id=wlist.id, word="didn't", context_sentence="He didn't forget.", position=1)
        w3 = Word(list_id=wlist.id, word="their", context_sentence="Their new puppy.", position=2)
        db.session.add_all([w1, w2, w3])

        student.lists.append(wlist)
        db.session.add(student)
        db.session.commit()

        return {
            'student_id': student.id,
            'list_id': wlist.id
        }

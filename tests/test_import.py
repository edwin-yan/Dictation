import pytest
from app.services.importer import (
    parse_csv_content,
    generate_import_preview,
    execute_import,
    DEFAULT_TEMPLATE_CSV
)
from app.models import db, WordListFolder, WordList, Word, Student


class TestCSVImport:
    """Test CSV parsing, template generation, preview, and execution."""

    def test_template_csv_structure(self):
        assert "folder,list_title,word,context_sentence" in DEFAULT_TEMPLATE_CSV
        assert "about" in DEFAULT_TEMPLATE_CSV
        assert "4th Grade Non-Negotiable" in DEFAULT_TEMPLATE_CSV

    def test_parse_csv_content_valid(self):
        csv_text = """folder,list_title,word,context_sentence
5th Grade Science,Planets,jupiter,Jupiter is the largest planet.
5th Grade Science,Planets,saturn,Saturn has beautiful rings.
"""
        rows, errors = parse_csv_content(csv_text)
        assert len(errors) == 0
        assert len(rows) == 2
        assert rows[0]['folder'] == '5th Grade Science'
        assert rows[0]['list_title'] == 'Planets'
        assert rows[0]['word'] == 'jupiter'
        assert rows[0]['context_sentence'] == 'Jupiter is the largest planet.'

    def test_generate_preview(self):
        csv_text = """folder,list_title,word,context_sentence
Grade 3,Week 1,cat,The cat meowed.
Grade 3,Week 1,dog,The dog barked.
Grade 3,Week 2,bird,The bird sang.
"""
        preview = generate_import_preview(csv_text)
        assert preview['success'] is True
        assert preview['total_rows'] == 3
        assert len(preview['folders']) == 1
        assert len(preview['lists']) == 2

    def test_execute_import(self, app):
        with app.app_context():
            student = Student(name="Import Tester", avatar="🌟")
            db.session.add(student)
            db.session.commit()

            rows = [
                {'folder': 'Custom Folder', 'list_title': 'Spelling List A', 'word': 'happy',
                 'context_sentence': 'I feel very happy.'},
                {'folder': 'Custom Folder', 'list_title': 'Spelling List A', 'word': 'joy',
                 'context_sentence': 'Jumping for joy.'},
                {'folder': 'Custom Folder', 'list_title': 'Spelling List B', 'word': 'peace',
                 'context_sentence': 'Living in peace.'},
            ]

            result = execute_import(rows)
            assert result['success'] is True
            assert result['created_folders'] == 1
            assert result['created_lists'] == 2
            assert result['created_words'] == 3

            # Verify database objects
            folder = WordListFolder.query.filter_by(name='Custom Folder').first()
            assert folder is not None
            assert folder.lists.count() == 2

            list_a = WordList.query.filter_by(title='Spelling List A').first()
            assert list_a is not None
            assert list_a.folder_id == folder.id
            assert list_a.words.count() == 2

            # Verify student association
            fetched_student = Student.query.filter_by(name="Import Tester").first()
            assert list_a in fetched_student.lists

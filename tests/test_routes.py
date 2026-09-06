import pytest
from flask import session
from app.models import db, Student, WordList, Word, ChallengeAttempt, MissedWord


class TestRoutes:
    """Test web application routes, workflows, and API endpoints."""

    def test_select_student_page(self, client, sample_data):
        response = client.get('/select-student')
        assert response.status_code == 200
        assert b"Who is practicing today?" in response.data
        assert b"Test Kid" in response.data

    def test_dashboard_with_student(self, client, sample_data):
        student_id = sample_data['student_id']
        response = client.get(f'/dashboard?student_id={student_id}')
        assert response.status_code == 200
        assert b"Hey Test Kid!" in response.data
        assert b"Test List" in response.data

    def test_study_cards_page(self, client, sample_data):
        list_id = sample_data['list_id']
        student_id = sample_data['student_id']
        response = client.get(f'/study/{list_id}?student_id={student_id}')
        assert response.status_code == 200
        assert b"Study Flashcards: Test List" in response.data
        assert b"Flip Card" in response.data

    def test_challenge_page(self, client, sample_data):
        list_id = sample_data['list_id']
        student_id = sample_data['student_id']
        response = client.get(f'/challenge/{list_id}?student_id={student_id}')
        assert response.status_code == 200
        assert b"Repeat" in response.data
        assert b"Next Word" in response.data

    def test_api_submit_challenge_and_results(self, client, sample_data):
        student_id = sample_data['student_id']
        list_id = sample_data['list_id']

        payload = {
            "student_id": student_id,
            "list_id": list_id,
            "test_type": "list",
            "title": "Test List",
            "answers": [
                {"word": "about", "context_sentence": "A book about stars.", "student_input": "about"},
                {"word": "didn't", "context_sentence": "He didn't forget.", "student_input": "didnt"},
                # missed apostrophe
                {"word": "their", "context_sentence": "Their new puppy.", "student_input": "  THEIR  "}
                # correct with spaces & caps
            ]
        }

        response = client.post('/api/test/submit', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['score'] == 2
        assert data['total'] == 3
        assert data['percentage'] == 66.7
        attempt_id = data['attempt_id']

        # Verify results page loads
        res_page = client.get(f'/results/{attempt_id}')
        assert res_page.status_code == 200
        assert b"66.7%" in res_page.data
        assert b"about" in res_page.data

    def test_admin_authentication_and_management(self, client, app):
        # Accessing admin without login redirects
        res = client.get('/admin/')
        assert res.status_code == 302
        assert '/admin/login' in res.location

        # Submit wrong password
        res_wrong = client.post('/admin/login', data={'password': 'wrongpassword'}, follow_redirects=True)
        assert b"Incorrect administrator password." in res_wrong.data

        # Submit correct password
        res_correct = client.post('/admin/login', data={'password': 'testadminpassword'}, follow_redirects=True)
        assert b"Administrator Management" in res_correct.data

        # Create new student as admin
        res_create_student = client.post('/admin/students/create', data={
            'name': 'New Star Student',
            'avatar': '🦄'
        }, follow_redirects=True)
        assert res_create_student.status_code == 200
        assert b"New Star Student" in res_create_student.data

        # Create new word list as admin
        res_create_list = client.post('/admin/lists/create', data={
            'title': 'Fun Friday Words',
            'description': 'End of week challenge',
            'category': 'Custom'
        }, follow_redirects=True)
        assert res_create_list.status_code == 200
        assert b"Fun Friday Words" in res_create_list.data

    def test_admin_delete_test_attempt(self, client, sample_data, app):
        from app.models import ChallengeAttempt, MissedWord, db
        student_id = sample_data['student_id']
        list_id = sample_data['list_id']

        # 1. Submit a test attempt
        payload = {
            "student_id": student_id,
            "list_id": list_id,
            "test_type": "list",
            "title": "Deletable Test Attempt",
            "answers": [
                {"word": "about", "context_sentence": "About stars.", "student_input": "wrongword"}
            ]
        }
        res_submit = client.post('/api/test/submit', json=payload)
        assert res_submit.status_code == 200
        attempt_id = res_submit.get_json()['attempt_id']

        # Verify attempt and missed word exist
        with app.app_context():
            assert db.session.get(ChallengeAttempt, attempt_id) is not None
            missed = MissedWord.query.filter_by(student_id=student_id, word="about").first()
            assert missed is not None
            assert missed.mistake_count >= 1

        # 2. Deletion without login should be blocked (redirects to login)
        res_unauth = client.post(f'/admin/history/{attempt_id}/delete')
        assert res_unauth.status_code == 302
        assert '/admin/login' in res_unauth.location

        # 3. Login as admin
        client.post('/admin/login', data={'password': 'testadminpassword'})

        # 4. Delete attempt
        res_del = client.post(f'/admin/history/{attempt_id}/delete', follow_redirects=True)
        assert res_del.status_code == 200
        assert b"has been deleted" in res_del.data

        # 5. Verify attempt is deleted in database
        with app.app_context():
            assert db.session.get(ChallengeAttempt, attempt_id) is None
            # Missed word created by this attempt should be cleaned up
            missed_after = MissedWord.query.filter_by(student_id=student_id, word="about").first()
            assert missed_after is None

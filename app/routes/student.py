from flask import Blueprint, render_template, request, redirect, url_for, make_response, flash, jsonify
from app.models import db, Student, WordListFolder, WordList, Word, ChallengeAttempt, ChallengeDetail, MissedWord
import random

student_bp = Blueprint('student', __name__)


@student_bp.route('/')
def index():
    student_id = request.args.get('student_id', type=int)
    if not student_id:
        cookie_id = request.cookies.get('dictation_student_id')
        if cookie_id and cookie_id.isdigit():
            student_id = int(cookie_id)

    if student_id:
        student = db.session.get(Student, student_id)
        if student:
            return redirect(url_for('student.dashboard', student_id=student.id))

    return redirect(url_for('student.select_student'))


@student_bp.route('/select-student')
def select_student():
    students = Student.query.order_by(Student.name).all()
    return render_template('select_student.html', students=students)


@student_bp.route('/dashboard')
def dashboard():
    students = Student.query.order_by(Student.name).all()
    if not students:
        return render_template('dashboard.html', students=[], current_student=None)

    student_id = request.args.get('student_id', type=int)
    if not student_id:
        cookie_id = request.cookies.get('dictation_student_id')
        if cookie_id and cookie_id.isdigit():
            student_id = int(cookie_id)

    current_student = None
    if student_id:
        current_student = db.session.get(Student, student_id)
    if not current_student:
        current_student = students[0]

    # Fetch assigned bundles for current student
    assigned_folders = current_student.folders.order_by(WordListFolder.position, WordListFolder.name).all()
    direct_lists = current_student.lists.order_by(WordList.id).all()
    
    folder_groups = []
    processed_list_ids = set()
    total_assigned_lists = 0

    for folder in assigned_folders:
        folder_lists = folder.lists.order_by(WordList.id).all()
        if folder_lists:
            enriched_lists = []
            for wlist in folder_lists:
                latest_attempt = ChallengeAttempt.query.filter_by(
                    student_id=current_student.id,
                    list_id=wlist.id
                ).order_by(ChallengeAttempt.created_at.desc()).first()

                enriched_lists.append({
                    'id': wlist.id,
                    'title': wlist.title,
                    'description': wlist.description,
                    'category': wlist.category,
                    'word_count': wlist.words.count(),
                    'latest_attempt': latest_attempt,
                    'words': wlist.words.all()
                })
                processed_list_ids.add(wlist.id)
                total_assigned_lists += 1

            folder_groups.append({
                'id': folder.id,
                'name': folder.name,
                'description': folder.description,
                'icon': folder.icon or '📁',
                'lists': enriched_lists
            })

    # Any standalone unfiled lists
    unfiled_lists = [l for l in direct_lists if l.id not in processed_list_ids]
    if unfiled_lists:
        enriched_unfiled = []
        for wlist in unfiled_lists:
            latest_attempt = ChallengeAttempt.query.filter_by(
                student_id=current_student.id,
                list_id=wlist.id
            ).order_by(ChallengeAttempt.created_at.desc()).first()

            enriched_unfiled.append({
                'id': wlist.id,
                'title': wlist.title,
                'description': wlist.description,
                'category': wlist.category,
                'word_count': wlist.words.count(),
                'latest_attempt': latest_attempt,
                'words': wlist.words.all()
            })
            total_assigned_lists += 1

        folder_groups.append({
            'id': 0,
            'name': 'Other Lists',
            'description': 'Additional study word lists',
            'icon': '📚',
            'lists': enriched_unfiled
        })

    # Fetch active missed words (Tricky Words)
    missed_words = MissedWord.query.filter_by(
        student_id=current_student.id,
        is_resolved=False
    ).order_by(MissedWord.mistake_count.desc(), MissedWord.last_tested_at.desc()).all()

    # Fetch recent challenge attempts
    recent_attempts = ChallengeAttempt.query.filter_by(
        student_id=current_student.id
    ).order_by(ChallengeAttempt.created_at.desc()).limit(10).all()

    # Stats calculation
    total_challenges = current_student.attempts.count()
    if total_challenges > 0:
        avg_score = sum([t.percentage for t in current_student.attempts.all()]) / total_challenges
    else:
        avg_score = 0.0

    resp = make_response(render_template(
        'dashboard.html',
        students=students,
        current_student=current_student,
        folder_groups=folder_groups,
        total_assigned_lists=total_assigned_lists,
        missed_words=missed_words,
        recent_attempts=recent_attempts,
        total_challenges=total_challenges,
        avg_score=round(avg_score, 1)
    ))

    resp.set_cookie('dictation_student_id', str(current_student.id), max_age=30 * 24 * 3600)
    return resp


@student_bp.route('/study/<int:list_id>')
def study_list(list_id):
    student_id = request.args.get('student_id', type=int)
    if not student_id:
        cookie_id = request.cookies.get('dictation_student_id')
        if cookie_id and cookie_id.isdigit():
            student_id = int(cookie_id)

    student = db.session.get(Student, student_id) if student_id else Student.query.first()
    word_list = db.session.get(WordList, list_id)
    if not word_list:
        flash("Word list not found.", "warning")
        return redirect(url_for('student.dashboard'))
    words = word_list.words.all()

    if not words:
        flash("This list has no words to study yet.", "info")
        return redirect(url_for('student.dashboard', student_id=student.id if student else None))

    words_data = [w.to_dict() for w in words]

    return render_template(
        'study_cards.html',
        student=student,
        word_list=word_list,
        words=words_data
    )


@student_bp.route('/challenge/<int:list_id>')
def take_challenge(list_id):
    student_id = request.args.get('student_id', type=int)
    if not student_id:
        cookie_id = request.cookies.get('dictation_student_id')
        if cookie_id and cookie_id.isdigit():
            student_id = int(cookie_id)

    student = db.session.get(Student, student_id) if student_id else Student.query.first()
    if not student:
        flash("Please select a student to start practicing.", "warning")
        return redirect(url_for('student.select_student'))

    word_list = db.session.get(WordList, list_id)
    if not word_list:
        flash("Word list not found.", "warning")
        return redirect(url_for('student.dashboard', student_id=student.id))
    words_query = word_list.words.all()

    if not words_query:
        flash("This list does not have any words yet.", "warning")
        return redirect(url_for('student.dashboard', student_id=student.id))

    words_data = [w.to_dict() for w in words_query]
    random.shuffle(words_data)

    return render_template(
        'test.html',
        student=student,
        word_list=word_list,
        test_type='list',
        test_title=word_list.title,
        words=words_data
    )


@student_bp.route('/challenge/tricky')
def take_tricky_challenge():
    student_id = request.args.get('student_id', type=int)
    if not student_id:
        cookie_id = request.cookies.get('dictation_student_id')
        if cookie_id and cookie_id.isdigit():
            student_id = int(cookie_id)

    student = db.session.get(Student, student_id) if student_id else Student.query.first()
    if not student:
        flash("Please select a student first.", "warning")
        return redirect(url_for('student.select_student'))

    missed = MissedWord.query.filter_by(
        student_id=student.id,
        is_resolved=False
    ).all()

    if not missed:
        flash("Awesome! You currently have zero tricky words in your practice queue.", "success")
        return redirect(url_for('student.dashboard', student_id=student.id))

    words_data = [{
        'id': mw.id,
        'word': mw.word,
        'context_sentence': mw.context_sentence or '',
        'position': idx
    } for idx, mw in enumerate(missed)]

    random.shuffle(words_data)

    return render_template(
        'test.html',
        student=student,
        word_list=None,
        test_type='missed_words',
        test_title='Tricky Words Quest',
        words=words_data
    )


@student_bp.route('/results/<int:attempt_id>')
def results(attempt_id):
    attempt = db.session.get(ChallengeAttempt, attempt_id)
    if not attempt:
        flash("Challenge results not found.", "warning")
        return redirect(url_for('student.dashboard'))
    details = attempt.details.all()

    return render_template(
        'results.html',
        attempt=attempt,
        student=attempt.student,
        details=details
    )

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime, timezone
import os
from app.models import db, Student, WordList, Word, ChallengeAttempt, ChallengeDetail, MissedWord
from app.services.grading import grade_spelling
from app.services.speech import synthesize_speech, DEFAULT_VOICE

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/audio/speak', methods=['GET'])
def stream_speech():
    """
    Streams neural TTS audio for a word and optional context sentence.
    Query params:
      - word: str (required)
      - context: str (optional)
      - speed: str (optional, default 'relaxed')
      - voice: str (optional, default 'en-US-AnaNeural')
    """
    word = request.args.get('word', '').strip()
    if not word:
        return jsonify({'error': 'Word parameter is required'}), 400

    context = request.args.get('context', '').strip()
    speed = request.args.get('speed', 'relaxed').strip()
    voice = request.args.get('voice', DEFAULT_VOICE).strip()

    try:
        mp3_path = synthesize_speech(word=word, context=context, speed=speed, voice=voice)
        if os.path.exists(mp3_path):
            response = send_file(mp3_path, mimetype='audio/mpeg')
            response.headers['Cache-Control'] = 'public, max-age=2592000'  # 30 days cache
            return response
        else:
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Speech synthesis failed: {str(e)}'}), 500


@api_bp.route('/test/submit', methods=['POST'])
def submit_test():
    """
    Submits a completed spelling dictation challenge.
    Payload:
    {
        "student_id": int,
        "list_id": int | null,
        "test_type": "list" | "missed_words",
        "title": str,
        "answers": [
            {
                "word": "about",
                "context_sentence": "...",
                "student_input": "about"
            },
            ...
        ]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    student_id = data.get('student_id')
    list_id = data.get('list_id')
    challenge_type = data.get('test_type', 'list')
    title = data.get('title', 'Spelling Challenge')
    answers = data.get('answers', [])

    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    if not answers:
        return jsonify({'error': 'No answers submitted'}), 400

    total_words = len(answers)
    correct_count = 0
    now = datetime.now(timezone.utc)

    # Create challenge attempt record
    attempt = ChallengeAttempt(
        student_id=student.id,
        list_id=list_id if list_id else None,
        challenge_type=challenge_type,
        title=title,
        score=0,
        total_words=total_words,
        percentage=0.0,
        created_at=now
    )
    db.session.add(attempt)
    db.session.flush()

    graded_results = []

    for item in answers:
        word_text = str(item.get('word', '')).strip()
        context_sentence = str(item.get('context_sentence', '')).strip()
        student_input = str(item.get('student_input', ''))

        is_correct = grade_spelling(student_input, word_text)
        if is_correct:
            correct_count += 1

        detail = ChallengeDetail(
            attempt_id=attempt.id,
            word=word_text,
            context_sentence=context_sentence,
            student_input=student_input,
            is_correct=is_correct
        )
        db.session.add(detail)

        # Update MissedWord tracking
        existing_missed = MissedWord.query.filter_by(
            student_id=student.id,
            word=word_text
        ).first()

        if not is_correct:
            if existing_missed:
                existing_missed.mistake_count += 1
                existing_missed.is_resolved = False
                existing_missed.mastery_score = 0
                existing_missed.last_tested_at = now
            else:
                new_missed = MissedWord(
                    student_id=student.id,
                    word=word_text,
                    context_sentence=context_sentence,
                    mistake_count=1,
                    is_resolved=False,
                    mastery_score=0,
                    last_tested_at=now
                )
                db.session.add(new_missed)
        else:
            if existing_missed and not existing_missed.is_resolved:
                existing_missed.mastery_score += 1
                existing_missed.last_tested_at = now
                if existing_missed.mastery_score >= 1:
                    existing_missed.is_resolved = True

        graded_results.append({
            'word': word_text,
            'context_sentence': context_sentence,
            'student_input': student_input,
            'is_correct': is_correct
        })

    attempt.score = correct_count
    attempt.percentage = round((correct_count / total_words) * 100.0, 1) if total_words > 0 else 0.0

    db.session.commit()

    return jsonify({
        'success': True,
        'attempt_id': attempt.id,
        'score': attempt.score,
        'total': total_words,
        'percentage': attempt.percentage,
        'redirect_url': f'/results/{attempt.id}'
    })


@api_bp.route('/students', methods=['GET'])
def get_students():
    students = Student.query.order_by(Student.name).all()
    return jsonify([s.to_dict() for s in students])


@api_bp.route('/lists', methods=['GET'])
def get_lists():
    lists = WordList.query.order_by(WordList.id).all()
    return jsonify([l.to_dict(include_words=True) for l in lists])

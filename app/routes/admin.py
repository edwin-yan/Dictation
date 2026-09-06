from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify, Response
import os
from app.models import db, Student, WordListFolder, WordList, Word, ChallengeAttempt, ChallengeDetail, MissedWord
from app.services.seeder import seed_database
from app.services.importer import (
    DEFAULT_TEMPLATE_CSV,
    LLM_PROMPT_TEMPLATE,
    generate_import_preview,
    execute_import
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in with the administrator password.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('is_admin'):
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        expected_password = str(
            current_app.config.get('ADMIN_PASSWORD') or os.getenv('ADMIN_PASSWORD') or 'admin123').strip()

        if password == expected_password:
            session['is_admin'] = True
            flash('Welcome, Administrator!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin.index'))
        else:
            flash('Incorrect administrator password.', 'danger')

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.pop('is_admin', None)
    flash('You have logged out of the admin area.', 'info')
    return redirect(url_for('student.select_student'))


@admin_bp.route('/')
@admin_required
def index():
    students_count = Student.query.count()
    folders_count = WordListFolder.query.count()
    lists_count = WordList.query.count()
    words_count = Word.query.count()
    attempts_count = ChallengeAttempt.query.count()

    recent_attempts = ChallengeAttempt.query.order_by(ChallengeAttempt.created_at.desc()).limit(8).all()
    students = Student.query.order_by(Student.name).all()
    folders = WordListFolder.query.order_by(WordListFolder.position, WordListFolder.name).all()
    word_lists = WordList.query.order_by(WordList.id).all()

    return render_template(
        'admin/index.html',
        students_count=students_count,
        folders_count=folders_count,
        lists_count=lists_count,
        words_count=words_count,
        attempts_count=attempts_count,
        recent_attempts=recent_attempts,
        students=students,
        folders=folders,
        word_lists=word_lists
    )


# --- Student Management ---

@admin_bp.route('/students', methods=['GET'])
@admin_required
def students():
    students_list = Student.query.order_by(Student.name).all()
    folders_list = WordListFolder.query.order_by(WordListFolder.position, WordListFolder.name).all()
    return render_template('admin/students.html', students=students_list, folders=folders_list)


@admin_bp.route('/students/create', methods=['POST'])
@admin_required
def create_student():
    name = request.form.get('name', '').strip()
    avatar = request.form.get('avatar', '🦊').strip()
    selected_folder_ids = request.form.getlist('folder_ids')

    if not name:
        flash('Student name is required.', 'danger')
        return redirect(url_for('admin.students'))

    if Student.query.filter_by(name=name).first():
        flash(f"A student named '{name}' already exists.", 'warning')
        return redirect(url_for('admin.students'))

    student = Student(name=name, avatar=avatar)

    if selected_folder_ids:
        for fid in selected_folder_ids:
            folder = db.session.get(WordListFolder, int(fid))
            if folder:
                student.folders.append(folder)
    else:
        for folder in WordListFolder.query.all():
            student.folders.append(folder)

    db.session.add(student)
    db.session.commit()
    flash(f"Student '{name}' added with {student.folders.count()} assigned bundles.", 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/students/<int:student_id>/edit', methods=['POST'])
@admin_required
def edit_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))

    name = request.form.get('name', '').strip()
    avatar = request.form.get('avatar', student.avatar).strip()
    selected_folder_ids = request.form.getlist('folder_ids')

    if not name:
        flash('Student name cannot be empty.', 'danger')
        return redirect(url_for('admin.students'))

    existing = Student.query.filter(Student.name == name, Student.id != student.id).first()
    if existing:
        flash(f"Another student named '{name}' already exists.", 'warning')
        return redirect(url_for('admin.students'))

    student.name = name
    student.avatar = avatar

    student.folders = []
    for fid in selected_folder_ids:
        folder = db.session.get(WordListFolder, int(fid))
        if folder:
            student.folders.append(folder)

    db.session.commit()
    flash(f"Student '{name}' updated successfully.", 'success')
    return redirect(url_for('admin.students'))


@admin_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student:
        name = student.name
        db.session.delete(student)
        db.session.commit()
        flash(f"Student '{name}' deleted.", 'info')
    return redirect(url_for('admin.students'))


# --- Bundle / Folder Management ---

@admin_bp.route('/folders/create', methods=['POST'])
@admin_required
def create_folder():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', '📁').strip()

    if not name:
        flash('Bundle name is required.', 'danger')
        return redirect(url_for('admin.lists'))

    pos = WordListFolder.query.count()
    folder = WordListFolder(name=name, description=description, icon=icon, position=pos)

    # Auto-associate new folder with all existing students
    for s in Student.query.all():
        s.folders.append(folder)

    db.session.add(folder)
    db.session.commit()
    flash(f"Bundle '{name}' created and connected to students.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/folders/<int:folder_id>/edit', methods=['POST'])
@admin_required
def edit_folder(folder_id):
    folder = db.session.get(WordListFolder, folder_id)
    if not folder:
        flash('Bundle not found.', 'danger')
        return redirect(url_for('admin.lists'))

    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', folder.icon).strip()

    if not name:
        flash('Bundle name cannot be empty.', 'danger')
        return redirect(url_for('admin.lists'))

    folder.name = name
    folder.description = description
    folder.icon = icon
    db.session.commit()
    flash(f"Bundle '{name}' updated.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/folders/<int:folder_id>/delete', methods=['POST'])
@admin_required
def delete_folder(folder_id):
    folder = db.session.get(WordListFolder, folder_id)
    if folder:
        name = folder.name
        db.session.delete(folder)
        db.session.commit()
        flash(f"Bundle '{name}' and all its lists removed.", 'info')
    return redirect(url_for('admin.lists'))


# --- Word List & Word Management ---

@admin_bp.route('/lists', methods=['GET'])
@admin_required
def lists():
    folders_list = WordListFolder.query.order_by(WordListFolder.position, WordListFolder.name).all()
    word_lists = WordList.query.order_by(WordList.id).all()
    students_list = Student.query.order_by(Student.name).all()
    return render_template('admin/lists.html', word_lists=word_lists, folders=folders_list, students=students_list)


@admin_bp.route('/lists/create', methods=['POST'])
@admin_required
def create_list():
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'Custom').strip()
    folder_id = request.form.get('folder_id', type=int)

    if not title:
        flash('List title is required.', 'danger')
        return redirect(url_for('admin.lists'))

    wlist = WordList(
        folder_id=folder_id if folder_id else None,
        title=title,
        description=description,
        category=category
    )
    db.session.add(wlist)
    db.session.commit()
    flash(f"Word list '{title}' created.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/lists/<int:list_id>/edit', methods=['POST'])
@admin_required
def edit_list(list_id):
    wlist = db.session.get(WordList, list_id)
    if not wlist:
        flash('List not found.', 'danger')
        return redirect(url_for('admin.lists'))

    title = request.form.get('title', '').strip()
    if not title:
        flash('List title cannot be empty.', 'danger')
        return redirect(url_for('admin.lists'))

    wlist.title = title
    wlist.description = request.form.get('description', '').strip()
    folder_id = request.form.get('folder_id', type=int)
    wlist.folder_id = folder_id if folder_id else None

    db.session.commit()
    flash(f"Word list '{wlist.title}' updated successfully.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/lists/<int:list_id>/delete', methods=['POST'])
@admin_required
def delete_list(list_id):
    wlist = db.session.get(WordList, list_id)
    if wlist:
        title = wlist.title
        db.session.delete(wlist)
        db.session.commit()
        flash(f"Word list '{title}' deleted.", 'info')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/lists/<int:list_id>/words/add', methods=['POST'])
@admin_required
def add_word(list_id):
    wlist = db.session.get(WordList, list_id)
    if not wlist:
        flash('List not found.', 'danger')
        return redirect(url_for('admin.lists'))

    word_text = request.form.get('word', '').strip()
    context = request.form.get('context_sentence', '').strip()

    if not word_text:
        flash('Word text is required.', 'danger')
        return redirect(url_for('admin.lists'))

    count = wlist.words.count()
    word_obj = Word(
        list_id=wlist.id,
        word=word_text,
        context_sentence=context if context else None,
        position=count
    )
    db.session.add(word_obj)
    db.session.commit()
    flash(f"Word '{word_text}' added to '{wlist.title}'.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/words/<int:word_id>/edit', methods=['POST'])
@admin_required
def edit_word(word_id):
    word_obj = db.session.get(Word, word_id)
    if not word_obj:
        flash('Word not found.', 'danger')
        return redirect(url_for('admin.lists'))

    word_text = request.form.get('word', '').strip()
    context = request.form.get('context_sentence', '').strip()

    if not word_text:
        flash('Word text cannot be empty.', 'danger')
        return redirect(url_for('admin.lists'))

    word_obj.word = word_text
    word_obj.context_sentence = context if context else None
    db.session.commit()
    flash(f"Word '{word_text}' updated.", 'success')
    return redirect(url_for('admin.lists'))


@admin_bp.route('/words/<int:word_id>/delete', methods=['POST'])
@admin_required
def delete_word(word_id):
    word_obj = db.session.get(Word, word_id)
    if word_obj:
        list_title = word_obj.word_list.title
        word_name = word_obj.word
        db.session.delete(word_obj)
        db.session.commit()
        flash(f"Word '{word_name}' removed from '{list_title}'.", 'info')
    return redirect(url_for('admin.lists'))


# --- CSV Import & LLM Helper ---

@admin_bp.route('/import', methods=['GET'])
@admin_required
def import_page():
    students_list = Student.query.order_by(Student.name).all()
    return render_template(
        'admin/import.html',
        students=students_list,
        llm_prompt_template=LLM_PROMPT_TEMPLATE
    )


@admin_bp.route('/import/template', methods=['GET'])
@admin_required
def download_template():
    return Response(
        DEFAULT_TEMPLATE_CSV,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=spelling_import_template.csv"}
    )


@admin_bp.route('/import/preview', methods=['POST'])
@admin_required
def preview_import():
    csv_text = ''
    if 'csv_file' in request.files and request.files['csv_file'].filename:
        file = request.files['csv_file']
        csv_text = file.read().decode('utf-8', errors='replace')
    else:
        csv_text = request.form.get('csv_text', '')

    result = generate_import_preview(csv_text)
    return jsonify(result)


@admin_bp.route('/import/execute', methods=['POST'])
@admin_required
def execute_csv_import():
    data = request.get_json()
    if not data or 'rows' not in data:
        return jsonify({'success': False, 'message': 'No data payload received.'}), 400

    rows = data.get('rows', [])
    student_ids = data.get('student_ids')

    result = execute_import(rows, student_ids)
    if result.get('success'):
        flash(
            f"Successfully imported {result['created_words']} words into {result['created_lists']} lists under {result['created_folders']} bundles!",
            'success')
    return jsonify(result)


# --- Bundle Association Matrix ---

@admin_bp.route('/assignments', methods=['GET', 'POST'])
@admin_bp.route('/associations', methods=['GET', 'POST'])
@admin_required
def assignments():
    if request.method == 'POST':
        students_all = Student.query.all()
        folders_all = WordListFolder.query.all()

        for s in students_all:
            s.folders = []
            for f in folders_all:
                key = f"assoc_{s.id}_{f.id}"
                if key in request.form:
                    s.folders.append(f)

        db.session.commit()
        flash('Student bundle associations updated successfully.', 'success')
        return redirect(url_for('admin.assignments'))

    students_list = Student.query.order_by(Student.name).all()
    folders_list = WordListFolder.query.order_by(WordListFolder.position, WordListFolder.name).all()
    
    assoc_map = {}
    for s in students_list:
        for f in s.folders:
            assoc_map[(s.id, f.id)] = True

    return render_template(
        'admin/assignments.html',
        students=students_list,
        folders=folders_list,
        assignment_map=assoc_map
    )


# --- Test History & Submission Log ---

@admin_bp.route('/history', methods=['GET'])
@admin_required
def history():
    student_id = request.args.get('student_id', type=int)
    list_id = request.args.get('list_id', type=int)

    query = ChallengeAttempt.query

    if student_id:
        query = query.filter_by(student_id=student_id)
    if list_id:
        query = query.filter_by(list_id=list_id)

    attempts = query.order_by(ChallengeAttempt.created_at.desc()).all()
    students_list = Student.query.order_by(Student.name).all()
    word_lists = WordList.query.order_by(WordList.id).all()

    return render_template(
        'admin/history.html',
        attempts=attempts,
        students=students_list,
        word_lists=word_lists,
        selected_student_id=student_id,
        selected_list_id=list_id
    )


@admin_bp.route('/history/<int:attempt_id>/delete', methods=['POST'])
@admin_required
def delete_attempt(attempt_id):
    attempt = db.session.get(ChallengeAttempt, attempt_id)
    if not attempt:
        flash('Test submission record not found.', 'danger')
        return redirect(url_for('admin.history'))

    student_name = attempt.student.name if attempt.student else "Student"
    test_title = attempt.title

    # Revert missed words introduced by this attempt
    for detail in attempt.details:
        if not detail.is_correct:
            existing_missed = MissedWord.query.filter_by(
                student_id=attempt.student_id,
                word=detail.word
            ).first()
            if existing_missed:
                existing_missed.mistake_count -= 1
                if existing_missed.mistake_count <= 0:
                    db.session.delete(existing_missed)

    db.session.delete(attempt)
    db.session.commit()

    flash(f"Test result for '{student_name}' ({test_title}) has been deleted.", 'success')

    referrer = request.referrer
    if referrer and '/results/' not in referrer:
        return redirect(referrer)
    return redirect(url_for('admin.history'))


@admin_bp.route('/cache-audio', methods=['POST'])
@admin_required
def cache_audio():
    from app.services.speech import pregenerate_all_audio
    res = pregenerate_all_audio()
    flash(
        f"Audio pre-generation complete: {res['cached_files']} audio files generated for {res['total_words']} vocabulary words (errors: {res['errors']}).",
        'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/reseed', methods=['POST'])
@admin_required
def reseed():
    seed_database(force=True)
    flash('Database re-seeded successfully from 4th Grade Non-negotiable List PDF and default data!', 'success')
    return redirect(url_for('admin.index'))

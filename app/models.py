from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def utc_now():
    return datetime.now(timezone.utc)


# Association table between students and word list folders/bundles
student_folders = db.Table(
    'student_folders',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    db.Column('folder_id', db.Integer, db.ForeignKey('word_list_folders.id', ondelete='CASCADE'), primary_key=True)
)

# Association table between students and standalone word lists (optional fallback)
student_lists = db.Table(
    'student_lists',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
    db.Column('list_id', db.Integer, db.ForeignKey('word_lists.id', ondelete='CASCADE'), primary_key=True)
)

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    avatar = db.Column(db.String(50), default='🦊')
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    # Associated bundles / folders
    folders = db.relationship('WordListFolder', secondary=student_folders,
                              backref=db.backref('students', lazy='dynamic'), lazy='dynamic')

    # Direct associated lists
    lists = db.relationship('WordList', secondary=student_lists, backref=db.backref('students', lazy='dynamic'),
                            lazy='dynamic')
    
    # Activity history
    attempts = db.relationship('ChallengeAttempt', backref='student', lazy='dynamic', cascade='all, delete-orphan',
                               order_by='desc(ChallengeAttempt.created_at)')
    missed_words = db.relationship('MissedWord', backref='student', lazy='dynamic', cascade='all, delete-orphan',
                                   order_by='desc(MissedWord.mistake_count)')

    def get_all_associated_lists(self):
        """Returns all lists from assigned folders plus direct lists."""
        folder_lists = []
        for folder in self.folders.all():
            folder_lists.extend(folder.lists.all())
        direct_lists = self.lists.all()
        # Unique list preservation
        seen = set()
        result = []
        for l in folder_lists + direct_lists:
            if l.id not in seen:
                seen.add(l.id)
                result.append(l)
        return result

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'avatar': self.avatar,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_challenges': self.attempts.count(),
            'missed_count': self.missed_words.filter_by(is_resolved=False).count(),
            'associated_folder_ids': [f.id for f in self.folders.all()],
            'associated_list_ids': [l.id for l in self.get_all_associated_lists()]
        }


class WordListFolder(db.Model):
    """Organizes word lists into top-level bundles/folders (e.g. '4th Grade', '5th Grade', 'Science Vocabulary')."""
    __tablename__ = 'word_list_folders'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(20), default='📁')
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    # Lists in this folder
    lists = db.relationship('WordList', backref='folder', lazy='dynamic', cascade='all, delete-orphan',
                            order_by='WordList.id')

    def to_dict(self, include_lists=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'icon': self.icon,
            'position': self.position,
            'list_count': self.lists.count(),
            'total_words': sum(l.words.count() for l in self.lists.all()),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_lists:
            data['lists'] = [l.to_dict(include_words=True) for l in self.lists.all()]
        return data


class WordList(db.Model):
    __tablename__ = 'word_lists'

    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('word_list_folders.id', ondelete='CASCADE'), nullable=True,
                          index=True)
    title = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), default='General')
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    words = db.relationship('Word', backref='word_list', lazy='dynamic', cascade='all, delete-orphan',
                            order_by='Word.position')
    attempts = db.relationship('ChallengeAttempt', backref='word_list', lazy='dynamic')

    def to_dict(self, include_words=False):
        data = {
            'id': self.id,
            'folder_id': self.folder_id,
            'folder_name': self.folder.name if self.folder else 'Unfiled',
            'title': self.title,
            'description': self.description or '',
            'category': self.category,
            'word_count': self.words.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_words:
            data['words'] = [w.to_dict() for w in self.words.all()]
        return data


class Word(db.Model):
    __tablename__ = 'words'

    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('word_lists.id', ondelete='CASCADE'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False)
    context_sentence = db.Column(db.Text, nullable=True)
    position = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'list_id': self.list_id,
            'word': self.word,
            'context_sentence': self.context_sentence or '',
            'position': self.position
        }


class ChallengeAttempt(db.Model):
    """Stores completed spelling dictation challenge sessions."""
    __tablename__ = 'challenge_attempts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    list_id = db.Column(db.Integer, db.ForeignKey('word_lists.id', ondelete='SET NULL'), nullable=True, index=True)
    challenge_type = db.Column(db.String(30), default='list')  # 'list' or 'missed_words'
    title = db.Column(db.String(150), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_words = db.Column(db.Integer, nullable=False, default=0)
    percentage = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, index=True)

    # Details
    details = db.relationship('ChallengeDetail', backref='attempt', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else 'Unknown',
            'list_id': self.list_id,
            'challenge_type': self.challenge_type,
            'title': self.title,
            'score': self.score,
            'total_words': self.total_words,
            'percentage': round(self.percentage, 1),
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else None
        }
        if include_details:
            data['details'] = [d.to_dict() for d in self.details.all()]
        return data


class ChallengeDetail(db.Model):
    """Stores individual word answers for a challenge session."""
    __tablename__ = 'challenge_details'

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('challenge_attempts.id', ondelete='CASCADE'), nullable=False,
                           index=True)
    word = db.Column(db.String(100), nullable=False)
    context_sentence = db.Column(db.Text, nullable=True)
    student_input = db.Column(db.String(100), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'attempt_id': self.attempt_id,
            'word': self.word,
            'context_sentence': self.context_sentence or '',
            'student_input': self.student_input or '',
            'is_correct': self.is_correct
        }


class MissedWord(db.Model):
    """Aggregates words a student struggled with for targeted practice."""
    __tablename__ = 'missed_words'
    __table_args__ = (db.UniqueConstraint('student_id', 'word', name='uq_student_missed_word'),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    word = db.Column(db.String(100), nullable=False)
    context_sentence = db.Column(db.Text, nullable=True)
    mistake_count = db.Column(db.Integer, default=1)
    mastery_score = db.Column(db.Integer, default=0)
    is_resolved = db.Column(db.Boolean, default=False)
    last_tested_at = db.Column(db.DateTime(timezone=True), default=utc_now)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'word': self.word,
            'context_sentence': self.context_sentence or '',
            'mistake_count': self.mistake_count,
            'mastery_score': self.mastery_score,
            'is_resolved': self.is_resolved,
            'last_tested_at': self.last_tested_at.strftime('%Y-%m-%d') if self.last_tested_at else None
        }

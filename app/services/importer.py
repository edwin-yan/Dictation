import csv
import io
from typing import List, Dict, Any, Tuple
from app.models import db, WordListFolder, WordList, Word, Student

DEFAULT_TEMPLATE_CSV = """folder,list_title,word,context_sentence
4th Grade Non-Negotiable,List 1 (Aug 28),about,We read a fascinating story about dolphins.
4th Grade Non-Negotiable,List 1 (Aug 28),addition,In addition to math we practice spelling every day.
4th Grade Non-Negotiable,List 1 (Aug 28),a lot,There were a lot of stars in the clear night sky.
4th Grade Non-Negotiable,List 2 (Sept 4),hear,I can hear the birds chirping outside the window.
4th Grade Non-Negotiable,List 2 (Sept 4),here,Please place your finished assignment right here.
4th Grade Non-Negotiable,List 2 (Sept 4),it's,It's a wonderful day for an outdoor experiment.
4th Grade Non-Negotiable,List 2 (Sept 4),its,The cat gently licked its soft fur.
5th Grade Science,Space & Earth,solar,The solar system revolves around the sun.
5th Grade Science,Space & Earth,orbit,The Earth completes its orbit in one year.
"""

LLM_PROMPT_TEMPLATE = """You are a helpful curriculum assistant. Please generate a spelling word list in CSV format for:
[INSERT YOUR TOPIC / GRADE LEVEL HERE, e.g. "4th Grade Tricky Homophones" or "5th Grade Science Vocabulary"]

Requirements:
1. Provide the output STRICTLY as raw CSV with NO markdown code fences or conversational text.
2. The first line MUST be the header:
folder,list_title,word,context_sentence
3. For homophones (words like hear/here, their/there/they're, to/too/two), provide a clear, kid-friendly context sentence that clarifies the meaning.
4. If a word does not need a context sentence, leave context_sentence blank.

Example format:
folder,list_title,word,context_sentence
4th Grade Non-Negotiable,List 1,about,We read a fascinating story about dolphins.
4th Grade Non-Negotiable,List 1,believe,I believe you can accomplish anything with practice.
4th Grade Non-Negotiable,List 2,their,The students packed their backpacks before the bell.
4th Grade Non-Negotiable,List 2,there,Look over there to see the colorful rainbow.
"""


def normalize_header(header_name: str) -> str:
    """Normalizes header field names for forgiving parsing."""
    h = header_name.strip().lower().replace(' ', '_').replace('-', '_')
    if h in ['folder', 'group', 'folder_name', 'group_name', 'category']:
        return 'folder'
    if h in ['list_title', 'list', 'title', 'list_name', 'word_list']:
        return 'list_title'
    if h in ['word', 'spelling_word', 'words', 'vocab']:
        return 'word'
    if h in ['context_sentence', 'context', 'sentence', 'example', 'context_sentences']:
        return 'context_sentence'
    return h


def parse_csv_content(csv_text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """
    Parses raw CSV string into a standardized list of row dicts:
    [{ 'folder': str, 'list_title': str, 'word': str, 'context_sentence': str }, ...]
    """
    rows = []
    errors = []

    if not csv_text or not csv_text.strip():
        return rows, ["CSV content is empty."]

    # Clean text (remove UTF-8 BOM if present)
    clean_text = csv_text.lstrip('\ufeff')
    reader = csv.reader(io.StringIO(clean_text))

    headers = None
    header_indices = {}

    for row_idx, raw_row in enumerate(reader, start=1):
        if not raw_row or all(not cell.strip() for cell in raw_row):
            continue  # Skip empty lines

        if headers is None:
            # First non-empty row is header
            headers = [normalize_header(col) for col in raw_row]
            for idx, h in enumerate(headers):
                header_indices[h] = idx

            # Fallback if standard headers not provided
            if 'word' not in header_indices:
                errors.append("Header must contain a 'word' column.")
                return [], errors
            continue

        # Extract values
        word_idx = header_indices.get('word', 0)
        word_val = raw_row[word_idx].strip() if word_idx < len(raw_row) else ''

        if not word_val:
            continue  # Skip rows without word

        list_idx = header_indices.get('list_title')
        list_val = raw_row[list_idx].strip() if (list_idx is not None and list_idx < len(raw_row)) else 'Imported List'
        if not list_val:
            list_val = 'Imported List'

        folder_idx = header_indices.get('folder')
        folder_val = raw_row[folder_idx].strip() if (
                folder_idx is not None and folder_idx < len(raw_row)) else 'General'
        if not folder_val:
            folder_val = 'General'

        context_idx = header_indices.get('context_sentence')
        context_val = raw_row[context_idx].strip() if (context_idx is not None and context_idx < len(raw_row)) else ''

        rows.append({
            'row_num': row_idx,
            'folder': folder_val,
            'list_title': list_val,
            'word': word_val,
            'context_sentence': context_val
        })

    return rows, errors


def generate_import_preview(csv_text: str) -> Dict[str, Any]:
    """Generates preview summary and row records before committing."""
    rows, errors = parse_csv_content(csv_text)

    if errors:
        return {
            'success': False,
            'errors': errors,
            'rows': [],
            'folders': [],
            'lists': []
        }

    folders = sorted(list(set(r['folder'] for r in rows)))
    lists = sorted(list(set(f"{r['folder']} ➜ {r['list_title']}" for r in rows)))

    return {
        'success': True,
        'total_rows': len(rows),
        'folders': folders,
        'lists': lists,
        'rows': rows,
        'errors': []
    }


def execute_import(rows: List[Dict[str, str]], student_ids: List[int] = None) -> Dict[str, Any]:
    """
    Commits validated rows into database:
    Creates/finds folders, lists, and words, and associates them to students.
    """
    if not rows:
        return {'success': False, 'message': 'No rows to import.'}

    created_folders = 0
    created_lists = 0
    created_words = 0

    # Cache folders in memory: name -> WordListFolder
    folder_map = {}
    for f in WordListFolder.query.all():
        folder_map[f.name.lower()] = f

    # Cache lists in memory: (folder_id, list_title) -> WordList
    list_map = {}
    for l in WordList.query.all():
        list_map[(l.folder_id, l.title.lower())] = l

    new_or_updated_lists = set()

    for r in rows:
        folder_name = r.get('folder', 'General').strip()
        list_title = r.get('list_title', 'Imported List').strip()
        word_text = r.get('word', '').strip()
        context_sentence = r.get('context_sentence', '').strip()

        if not word_text:
            continue

        # 1. Resolve Folder
        folder_obj = folder_map.get(folder_name.lower())
        if not folder_obj:
            folder_obj = WordListFolder(name=folder_name, description=f"Imported category: {folder_name}")
            db.session.add(folder_obj)
            db.session.flush()
            folder_map[folder_name.lower()] = folder_obj
            created_folders += 1

        # 2. Resolve WordList
        list_key = (folder_obj.id, list_title.lower())
        wlist_obj = list_map.get(list_key)
        if not wlist_obj:
            wlist_obj = WordList(
                folder_id=folder_obj.id,
                title=list_title,
                description=f"Imported list under {folder_name}",
                category=folder_name
            )
            db.session.add(wlist_obj)
            db.session.flush()
            list_map[list_key] = wlist_obj
            created_lists += 1

        new_or_updated_lists.add(wlist_obj)

        # 3. Resolve Word (avoid duplicate word within the same list)
        existing_word = Word.query.filter_by(list_id=wlist_obj.id, word=word_text).first()
        if not existing_word:
            pos = wlist_obj.words.count()
            word_obj = Word(
                list_id=wlist_obj.id,
                word=word_text,
                context_sentence=context_sentence if context_sentence else None,
                position=pos
            )
            db.session.add(word_obj)
            created_words += 1
        else:
            # Update context if provided and not previously set
            if context_sentence and not existing_word.context_sentence:
                existing_word.context_sentence = context_sentence

    # 4. Associate lists with students
    students = Student.query.all()
    if student_ids:
        students = [s for s in students if s.id in student_ids]

    for s in students:
        for wlist in new_or_updated_lists:
            if wlist not in s.lists:
                s.lists.append(wlist)

    db.session.commit()

    return {
        'success': True,
        'created_folders': created_folders,
        'created_lists': created_lists,
        'created_words': created_words,
        'total_lists_affected': len(new_or_updated_lists)
    }

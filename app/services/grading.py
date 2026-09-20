import re
import unicodedata


def normalize_spelling(text: str, allow_multiple_words: bool = True) -> str:
    """
    Normalizes a spelling submission or target word:
    - Strips leading and trailing whitespace
    - Replaces smart/curly apostrophes and quotes with standard ASCII apostrophe
    - Normalizes unicode characters (NFKD)
    - If allow_multiple_words is False, strips all whitespace completely
    - If allow_multiple_words is True, collapses multiple internal whitespaces into a single space
    - Converts to lowercase
    """
    if text is None:
        return ""

    # Convert to string and normalize unicode
    text = str(text)
    text = unicodedata.normalize('NFKD', text)

    # Replace smart apostrophes / curly quotes
    text = text.replace('’', "'").replace('‘', "'").replace('`', "'").replace('´', "'")

    if not allow_multiple_words:
        # Strip all whitespaces and dots completely (e.g. "acc ident", "acc.ident", or "accident." -> "accident")
        text = re.sub(r'[\s.]+', '', text)
    else:
        # Strip trailing periods, trim, and collapse multiple spaces
        text = text.strip().rstrip('.')
        text = re.sub(r'\s+', ' ', text)

    # Case fold to lowercase
    return text.lower()


def grade_spelling(student_input: str, expected_word: str, allow_multiple_words: bool = None) -> bool:
    """
    Grades a student's spelling input against the expected word.
    If allow_multiple_words is False, spaces are completely stripped from both
    the student input and expected word.
    If allow_multiple_words is None (auto-detect), it defaults to True if expected_word
    contains an internal space, otherwise False.
    """
    if allow_multiple_words is None:
        expected_has_space = bool(expected_word and ' ' in expected_word.strip())
        allow_multiple_words = expected_has_space

    norm_input = normalize_spelling(student_input, allow_multiple_words=allow_multiple_words)
    norm_expected = normalize_spelling(expected_word, allow_multiple_words=allow_multiple_words)

    if not norm_expected:
        return False

    return norm_input == norm_expected


def grade_test_submission(answers: list, allow_multiple_words: bool = None) -> dict:
    """
    Grades a list of submitted answer dictionaries:
    Each item: { 'word': str, 'student_input': str, 'context_sentence': str (optional) }
    
    Returns:
    {
        'score': int,
        'total': int,
        'percentage': float,
        'results': [
            {
                'word': str,
                'context_sentence': str,
                'student_input': str,
                'is_correct': bool
            },
            ...
        ]
    }
    """
    results = []
    correct_count = 0

    for item in answers:
        word = item.get('word', '').strip()
        context = item.get('context_sentence', '').strip()
        student_input = item.get('student_input', '')

        is_correct = grade_spelling(student_input, word, allow_multiple_words=allow_multiple_words)
        if is_correct:
            correct_count += 1

        results.append({
            'word': word,
            'context_sentence': context,
            'student_input': student_input,
            'is_correct': is_correct
        })

    total = len(results)
    percentage = (correct_count / total * 100.0) if total > 0 else 0.0

    return {
        'score': correct_count,
        'total': total,
        'percentage': round(percentage, 1),
        'results': results
    }

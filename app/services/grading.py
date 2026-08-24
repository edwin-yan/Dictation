import re
import unicodedata


def normalize_spelling(text: str) -> str:
    """
    Normalizes a spelling submission or target word:
    - Strips leading and trailing whitespace
    - Replaces smart/curly apostrophes and quotes with standard ASCII apostrophe
    - Normalizes unicode characters (NFKD)
    - Collapses multiple internal whitespaces into a single space
    - Converts to lowercase
    """
    if text is None:
        return ""

    # Convert to string and normalize unicode
    text = str(text)
    text = unicodedata.normalize('NFKD', text)

    # Replace smart apostrophes / curly quotes
    text = text.replace('’', "'").replace('‘', "'").replace('`', "'").replace('´', "'")

    # Strip whitespace and collapse multiple spaces (e.g. "a   lot" -> "a lot")
    text = re.sub(r'\s+', ' ', text.strip())

    # Case fold to lowercase
    return text.lower()


def grade_spelling(student_input: str, expected_word: str) -> bool:
    """
    Grades a student's spelling input against the expected word.
    Returns True if the normalized input matches the normalized expected word.
    """
    norm_input = normalize_spelling(student_input)
    norm_expected = normalize_spelling(expected_word)

    if not norm_expected:
        return False

    return norm_input == norm_expected


def grade_test_submission(answers: list) -> dict:
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

        is_correct = grade_spelling(student_input, word)
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

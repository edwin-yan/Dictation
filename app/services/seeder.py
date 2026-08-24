import os
from pathlib import Path
import pypdf
from datetime import datetime, timedelta, timezone
from app.models import db, Student, WordListFolder, WordList, Word, ChallengeAttempt, ChallengeDetail, MissedWord

# High quality context sentences for homophones and vocabulary
CONTEXT_SENTENCES = {
    # List 1
    "about": "We read a fascinating story about dolphins.",
    "addition": "In addition to math, we practice spelling every day.",
    "a lot": "There were a lot of stars visible in the clear night sky.",
    "again": "Please read the directions again before starting.",
    "although": "Although it rained, the soccer game continued.",
    "always": "Always remember to double-check your spelling.",
    "answer": "Raise your hand if you know the answer.",
    "are": "We are ready to start our spelling adventure.",
    "around": "The children gathered around the teacher for story time.",
    "asked": "She asked a great question about solar energy.",
    "awesome": "That was an awesome performance at the talent show.",
    "beautiful": "The sunset over the mountains was beautiful.",
    "because": "We stayed inside because of the thunderstorm.",
    "before": "Wash your hands before eating lunch.",
    "beginning": "The story was exciting right from the beginning.",
    "believe": "I believe you can accomplish anything with practice.",
    "bought": "Mom bought fresh fruit at the grocery store.",
    "decided": "Our class decided on a name for the class pet.",
    "definitely": "We will definitely finish our project on time.",
    "didn't": "He didn't forget his homework folder today.",
    "different": "Every student has a different creative idea.",
    "does": "Does anyone know what time the bell rings?",
    "eventually": "With consistent practice, you will eventually master every word.",

    # List 2
    "every": "We practice spelling words every morning.",
    "example": "Can you give an example of a complete sentence?",
    "favorite": "Science is my favorite subject this semester.",
    "feel": "I feel confident about today's spelling challenge.",
    "finally": "After weeks of hard work, we finally finished the book.",
    "friend": "A true friend is always kind and supportive.",
    "furthermore": "She won the race; furthermore, she set a new record.",
    "turthermore": "She won the race; furthermore, she set a new record.",
    "hear": "I can hear the birds chirping outside the window.",
    "here": "Please place your finished notebook right here.",
    "hopefully": "Hopefully the weather will stay pleasant for recess.",
    "instance": "For instance, dogs and wolves are in the same animal family.",
    "interesting": "We learned an interesting fact about space exploration.",
    "it's": "It's a wonderful day for an outdoor science experiment.",
    "its": "The mother cat gently groomed its playful kitten.",
    "knew": "He knew all the answers on the spelling game.",
    "know": "Do you know how many continents there are?",
    "our": "This bright and welcoming room is our classroom.",
    "people": "Many people attended the school open house.",
    "probably": "It will probably rain later this afternoon.",
    "really": "The teacher was really proud of our team's effort.",
    "received": "Every student received a certificate of achievement.",
    "responsibility": "Taking care of your supplies is your personal responsibility.",
    "said": "The teacher said we did an amazing job today.",

    # List 3
    "school": "Our school has a wonderful library full of adventures.",
    "special": "Today is a special celebration for all the word masters.",
    "stopped": "The yellow school bus stopped safely at the crosswalk.",
    "surprise": "We planned a joyful surprise party for our teacher.",
    "their": "The students neatly organized their desks before leaving.",
    "there": "Look over there to see the colorful rainbow.",
    "they're": "They're studying hard for the upcoming spelling quest.",
    "thought": "She thought carefully before writing her sentence.",
    "threw": "The pitcher threw the ball to first base.",
    "through": "We walked through the garden path to the gazebo.",
    "to": "Let's walk together to the library.",
    "too": "I would love to join the reading club too.",
    "two": "I have two sharp pencils and an eraser.",
    "tried": "He tried three different strategies to solve the puzzle.",
    "until": "Please wait quietly until the teacher gives instructions.",
    "went": "Yesterday our whole class went on a field trip.",
    "we're": "We're excited to showcase what we learned this week.",
    "were": "They were enthusiastic during the science lab experiment.",
    "what": "What is your favorite book in the classroom?",
    "when": "When the bell chimes, it is time to line up.",
    "where": "Where did you find that interesting rock sample?",
    "would": "Would you please pass the colored markers?",
    "you're": "You're showing tremendous growth in your spelling skills."
}

FALLBACK_LISTS = {
    "List 1": {
        "title": "4th Grade List 1 (Aug 28th)",
        "description": "Essential 4th grade high-frequency words for everyday communication.",
        "category": "4th Grade Non-Negotiable",
        "words": [
            "about", "addition", "a lot", "again", "although", "always", "answer",
            "are", "around", "asked", "awesome", "beautiful", "because", "before",
            "beginning", "believe", "bought", "decided", "definitely", "didn't",
            "different", "does", "eventually"
        ]
    },
    "List 2": {
        "title": "4th Grade List 2 (Sept 4th)",
        "description": "4th grade list with tricky homophones (hear/here, it's/its, knew/know) and contractions.",
        "category": "4th Grade Non-Negotiable",
        "words": [
            "every", "example", "favorite", "feel", "finally", "friend", "furthermore",
            "hear", "here", "hopefully", "instance", "interesting", "it's", "its",
            "knew", "know", "our", "people", "probably", "really", "received",
            "responsibility", "said"
        ]
    },
    "List 3": {
        "title": "4th Grade List 3 (Sept 11th)",
        "description": "4th grade list featuring critical homophones (their/there/they're, to/too/two, we're/were/where, you're).",
        "category": "4th Grade Non-Negotiable",
        "words": [
            "school", "special", "stopped", "surprise", "their", "there", "they're",
            "thought", "threw", "through", "to", "too", "tried", "two", "until",
            "went", "we're", "were", "what", "when", "where", "would", "you're"
        ]
    }
}


def parse_pdf_lists(pdf_path: str = "4th Grade Non-negotiation List.pdf") -> dict:
    if not os.path.exists(pdf_path):
        return FALLBACK_LISTS

    try:
        reader = pypdf.PdfReader(pdf_path)
        if not reader.pages:
            return FALLBACK_LISTS

        text = reader.pages[0].extract_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        list1_words, list2_words, list3_words = [], [], []
        start_parsing = False

        for line in lines:
            if "about" in line.lower() and "every" in line.lower():
                start_parsing = True

            if start_parsing:
                cleaned = line.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
                parts = cleaned.split()
                if "a lot" in cleaned.lower():
                    list1_words.append("a lot")
                    idx = cleaned.lower().find("a lot") + 5
                    rem = cleaned[idx:].strip().split()
                    if len(rem) >= 1: list2_words.append(rem[0])
                    if len(rem) >= 2: list3_words.append(rem[1])
                elif len(parts) >= 3:
                    w1, w2, w3 = parts[0], parts[1], parts[2]
                    if w1.lower() == "to": w1 = "to"
                    if w2.lower() == "turthermore": w2 = "furthermore"
                    if w3.lower() == "to": w3 = "to"
                    list1_words.append(w1.lower())
                    list2_words.append(w2.lower())
                    list3_words.append(w3.lower())

        if list1_words and list2_words and list3_words:
            return {
                "List 1": {
                    "title": "4th Grade List 1 (Aug 28th)",
                    "description": "Essential 4th grade high-frequency spelling words from 4th Grade Non-negotiable List.",
                    "category": "4th Grade Non-Negotiable",
                    "words": list1_words
                },
                "List 2": {
                    "title": "4th Grade List 2 (Sept 4th)",
                    "description": "4th grade list with tricky homophones (hear/here, it's/its, knew/know).",
                    "category": "4th Grade Non-Negotiable",
                    "words": list2_words
                },
                "List 3": {
                    "title": "4th Grade List 3 (Sept 11th)",
                    "description": "4th grade list with key homophones (their/there/they're, to/too/two, we're/were).",
                    "category": "4th Grade Non-Negotiable",
                    "words": list3_words
                }
            }
    except Exception as e:
        print(f"Notice: PDF parse encountered {e}, using fallback structured list data.")

    return FALLBACK_LISTS


def seed_database(app=None, force=False):
    """
    Seeds initial folders, word lists, words, students, associations, and mock study histories.
    """
    if force:
        db.drop_all()
        db.create_all()
    else:
        db.create_all()

    # Check if already seeded
    if Student.query.first() and WordList.query.first() and not force:
        print("Database already contains data. Skipping seed.")
        return

    print("Seeding database with 4th Grade folders, lists, and student profiles...")

    # 1. Create Default Folder: "4th Grade Non-Negotiable"
    grade4_folder = WordListFolder(
        name="4th Grade Non-Negotiable",
        description="Official high-frequency spelling and non-negotiable lists for 4th Grade.",
        icon="📘",
        position=0
    )
    db.session.add(grade4_folder)
    db.session.flush()

    # 2. Parse or load lists
    lists_data = parse_pdf_lists("4th Grade Non-negotiation List.pdf")
    created_lists = {}

    for key, data in lists_data.items():
        wlist = WordList(
            folder_id=grade4_folder.id,
            title=data["title"],
            description=data["description"],
            category=data["category"]
        )
        db.session.add(wlist)
        db.session.flush()

        created_lists[key] = wlist

        for pos, word_text in enumerate(data["words"]):
            clean_word = word_text.strip()
            context = CONTEXT_SENTENCES.get(clean_word.lower(), f"Please spell the word '{clean_word}'.")

            word_obj = Word(
                list_id=wlist.id,
                word=clean_word,
                context_sentence=context,
                position=pos
            )
            db.session.add(word_obj)

    # 3. Seed Mock Students
    mock_students = [
        {"name": "Alex Carter", "avatar": "🚀"},
        {"name": "Emma Watson", "avatar": "🌟"},
        {"name": "Lucas Rivera", "avatar": "🦁"},
        {"name": "Maya Chen", "avatar": "🎨"},
    ]

    created_students = []
    for s_info in mock_students:
        student = Student(
            name=s_info["name"],
            avatar=s_info["avatar"]
        )
        # Associate folder/bundle with student
        student.folders.append(grade4_folder)

        db.session.add(student)
        db.session.flush()
        created_students.append(student)

    # 4. Seed Sample Historical Practice Records for Alex & Emma
    now = datetime.now(timezone.utc)
    alex = created_students[0]
    list1 = created_lists["List 1"]

    attempt_alex = ChallengeAttempt(
        student_id=alex.id,
        list_id=list1.id,
        challenge_type="list",
        title=list1.title,
        score=19,
        total_words=23,
        percentage=82.6,
        created_at=now - timedelta(days=1, hours=2)
    )
    db.session.add(attempt_alex)
    db.session.flush()

    missed_alex_words = [
        ("definitely", "definatly", CONTEXT_SENTENCES.get("definitely")),
        ("bought", "bot", CONTEXT_SENTENCES.get("bought")),
        ("a lot", "alot", CONTEXT_SENTENCES.get("a lot")),
        ("believe", "beleive", CONTEXT_SENTENCES.get("believe")),
    ]

    for w_obj in list1.words.all():
        mis = next((m for m in missed_alex_words if m[0] == w_obj.word.lower()), None)
        if mis:
            detail = ChallengeDetail(
                attempt_id=attempt_alex.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                student_input=mis[1],
                is_correct=False
            )
            mw = MissedWord(
                student_id=alex.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                mistake_count=1,
                is_resolved=False,
                last_tested_at=now - timedelta(days=1, hours=2)
            )
            db.session.add(mw)
        else:
            detail = ChallengeDetail(
                attempt_id=attempt_alex.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                student_input=w_obj.word,
                is_correct=True
            )
        db.session.add(detail)

    # Emma: List 2 Challenge
    emma = created_students[1]
    list2 = created_lists["List 2"]

    attempt_emma = ChallengeAttempt(
        student_id=emma.id,
        list_id=list2.id,
        challenge_type="list",
        title=list2.title,
        score=21,
        total_words=23,
        percentage=91.3,
        created_at=now - timedelta(hours=5)
    )
    db.session.add(attempt_emma)
    db.session.flush()

    missed_emma_words = [
        ("hear", "here", CONTEXT_SENTENCES.get("hear")),
        ("responsibility", "responsability", CONTEXT_SENTENCES.get("responsibility")),
    ]

    for w_obj in list2.words.all():
        mis = next((m for m in missed_emma_words if m[0] == w_obj.word.lower()), None)
        if mis:
            detail = ChallengeDetail(
                attempt_id=attempt_emma.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                student_input=mis[1],
                is_correct=False
            )
            mw = MissedWord(
                student_id=emma.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                mistake_count=1,
                is_resolved=False,
                last_tested_at=now - timedelta(hours=5)
            )
            db.session.add(mw)
        else:
            detail = ChallengeDetail(
                attempt_id=attempt_emma.id,
                word=w_obj.word,
                context_sentence=w_obj.context_sentence,
                student_input=w_obj.word,
                is_correct=True
            )
        db.session.add(detail)

    db.session.commit()
    print("Database seeding successfully completed!")

# ✏️ SpellMaster - Responsive Spelling Dictation & Study Web App

A modern, responsive spelling dictation and vocabulary study web application designed specifically for elementary
students (optimized for iPads, Chromebooks, and laptops). Packaged as a lightweight Docker container with local volume
persistence for a Proxmox intranet environment.

---

## 🌟 Key Features

1. **Student Study & Learning Hub**:
    - **Student Profile Picker**: Friendly profile selection with fun emoji avatars—no passwords needed for kids.
    - **🎴 3D Interactive Flashcards**: Study mode with animated flip cards, crystal-clear audio pronunciation, and
      contextual sentences before attempting dictation.
    - **🎧 Dictation Spelling Quest**: Distraction-free listen-and-spell interface with big "Repeat Audio" button (
      `Ctrl+Space`), autofocus, keyboard advancement, progress bar, and strictly hidden feedback during the activity.
    - **🌟 Tricky Words Auto-Aggregator**: Automatically collects and tracks words the student missed in past quests for
      focused practice and mastery.
    - **Encouraging Results**: Score gauges, stars, comparison breakdown, and audio replay for every word.

2. **High-Fidelity Neural TTS & Pacing Control**:
    - Uses Microsoft Azure Neural Text-to-Speech (`edge-tts`, zero API keys / zero cost, local mp3 cache) with friendly
      child voice `en-US-AnaNeural` and clear studio voices.
    - Global Speech Speed Selector in the top navigation (`Slow 0.70x`, `Kid-Friendly 0.80x`, `Standard 0.90x`,
      `Faster 1.05x`) with instant playback synchronization and `localStorage` persistence.
    - Natural cadence for words with context sentences:
      $$\text{[Word]} \xrightarrow{\text{500ms pause}} \text{[Context Sentence]} \xrightarrow{\text{500ms pause}} \text{[Word]}$$
    - Browser Web Speech API as an automatic offline fallback.

3. **Folder / Category Organization for Word Lists**:
    - Group word lists under folders (e.g. 📘 *4th Grade Non-Negotiable*, 🔬 *5th Grade Science*, 🚀 *Challenge Words*).
    - Neatly rendered folder sections on the student dashboard with badges and word counts.
    - Folder creation and organization in the Admin portal.

4. **CSV Import with Interactive Preview & LLM Prompt Helper**:
    - **CSV Template Download (`/admin/import/template`)**: Download pre-formatted `spelling_import_template.csv` (
      `folder,list_title,word,context_sentence`).
    - **LLM Prompt Helper**: One-click copyable prompt for ChatGPT / Claude / Gemini to generate spelling lists
      effortlessly.
    - **Live Preview & Confirmation**: 2-step verification table allows reviewing, editing, or deleting rows before
      saving to the database.

5. **Forgiving Grading Engine**:
    - Case-insensitive matching (`About` = `about`).
    - Strips leading and trailing whitespace.
    - Normalizes smart quotes and apostrophes (`didn’t` = `didn't`).
    - Normalizes multi-word internal whitespace (`a   lot` = `a lot`).

6. **Simple Admin Portal**:
    - Accessed via top-right lock icon with simple password (default: `admin123`, configurable via `.env`).
    - Manage students, avatars, folders, word lists, and words with context sentences.
    - One-click list association matrix for assigning lists to students.
    - School/classroom test submission log and database reset/reseed.

7. **Proxmox Intranet Docker Deployment & Persistence**:
    - Persistent local volume mount `./data:/app/data` ensures zero data loss during container updates or rebuilds.
    - Production WSGI deployment with Gunicorn.

---

## 🚀 Quick Start (Local Development)

### 1. Prerequisites & Conda Environment

Activate the specified Conda environment:

```bash
/Users/shaohua/miniconda3/condabin/conda activate flask
```

### 2. Environment Configuration

```bash
cp .env.example .env
```

### 3. Seed Database

Extracts 4th Grade word lists from `4th Grade Non-negotiation List.pdf`, creates default folders, and seeds sample
students:

```bash
python seed.py --force
```

### 4. Run Locally

```bash
python run.py
```

Open your browser at **`http://localhost:5001`**.

---

## 🐳 Docker Deployment (Proxmox Intranet)

### Run with Docker Compose

```bash
docker-compose up -d --build
```

The application will be accessible on port `5000` on your server's IP (e.g. `http://192.168.1.100:5000`).

### Persistent Volume

All SQLite database records and audio cache files are stored in `./data/dictation.db` and `./data/audio_cache/`, bound
to `/app/data` inside the container.

---

## 🧪 Running Pytest Tests

Run the full test suite verifying forgiving grading, models, auth, CSV import, and neural TTS:

```bash
pytest -v
```

---

## 📁 Project Structure

```
Dictation/
├── 4th Grade Non-negotiation List.pdf   # Source 4th Grade non-negotiable lists
├── app/
│   ├── __init__.py                     # Flask application factory
│   ├── config.py                       # App configuration & DB path resolver
│   ├── models.py                       # Models: Student, WordListFolder, WordList, Word, ChallengeAttempt, MissedWord
│   ├── routes/
│   │   ├── student.py                  # Student dashboard, flashcard study, spelling quest, results
│   │   ├── admin.py                    # Admin portal, students, lists, folders, CSV import, associations
│   │   └── api.py                      # REST endpoints & neural audio streaming (/api/audio/speak)
│   ├── services/
│   │   ├── grading.py                  # Forgiving grading logic & normalization
│   │   ├── speech.py                   # Server-side Microsoft Neural TTS generator & audio cache
│   │   ├── importer.py                 # CSV parser, template generator & LLM prompt helper
│   │   └── seeder.py                   # PDF parser & seed database utility
│   ├── static/
│   │   ├── css/style.css               # Responsive design system
│   │   └── js/
│   │       ├── app.js                  # Global UI helpers
│   │       ├── speech.js               # Hybrid neural + Web Speech audio engine
│   │       ├── test_runner.js          # Interactive spelling quest runner
│   │       └── admin.js                # Admin interactive modal helpers
│   └── templates/
│       ├── base.html                   # Base HTML layout with global speed control
│       ├── select_student.html         # Friendly profile picker
│       ├── dashboard.html              # Student dashboard organized by folder
│       ├── study_cards.html            # 3D interactive flashcards
│       ├── test.html                   # Spelling dictation quest
│       ├── results.html                # Quest results & review
│       └── admin/                      # Admin views & CSV import
├── data/                               # Local persistent volume directory (SQLite DB + audio cache)
├── tests/                              # Pytest test suite (28 unit tests)
├── Dockerfile                          # Container specification
├── docker-compose.yml                  # Docker Compose configuration
├── requirements.txt                    # Python dependencies
├── seed.py                             # Standalone seeding CLI
└── run.py                              # App entrypoint
```

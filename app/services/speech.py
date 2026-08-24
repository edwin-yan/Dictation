import os
import hashlib
import asyncio
from pathlib import Path
from flask import current_app

# Default voice choices
DEFAULT_VOICE = "en-US-AnaNeural"  # Friendly, natural youth voice for elementary learning
BACKUP_VOICES = {
    "ana": "en-US-AnaNeural",  # Friendly & clear child voice
    "jenny": "en-US-JennyNeural",  # Expressive female voice
    "guy": "en-US-GuyNeural",  # Clear male voice
    "aria": "en-US-AriaNeural"  # Confident female voice
}

# Speed mappings
SPEED_RATES = {
    "slow": "-25%",  # ~0.75x speed - extra slow for tricky words / young kids
    "relaxed": "-15%",  # ~0.85x speed - comfortable default for kids
    "normal": "-5%",  # ~0.95x speed
    "fast": "+5%"  # ~1.05x speed
}


def get_audio_cache_dir() -> Path:
    """Returns the persistent audio cache directory."""
    try:
        from app.config import BASE_DIR
        cache_dir = BASE_DIR / 'data' / 'audio_cache'
    except Exception:
        cache_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'audio_cache'

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def generate_cache_key(word: str, context: str = "", speed: str = "relaxed", voice: str = DEFAULT_VOICE) -> str:
    """Generates a stable sha256 hash key for audio caching."""
    raw = f"{word.strip().lower()}|{context.strip().lower()}|{speed.lower()}|{voice}".encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


async def _synthesize_edge_tts(text: str, voice: str, rate: str, output_path: str):
    """Asynchronously calls edge_tts to synthesize speech and save to mp3."""
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)


def synthesize_speech(word: str, context: str = "", speed: str = "relaxed", voice: str = DEFAULT_VOICE) -> str:
    """
    Generates or retrieves cached high-quality neural speech mp3 file.
    Cadence:
    - With context: "[Word]. ... [Context Sentence]. ... [Word]."
    - Without context: "[Word]."
    
    Returns: absolute file path to the mp3 audio file.
    """
    clean_word = (word or "").strip()
    clean_context = (context or "").strip()

    if not clean_word:
        raise ValueError("Cannot synthesize empty word.")

    # Resolve voice
    selected_voice = BACKUP_VOICES.get(voice.lower(), voice) if voice else DEFAULT_VOICE

    # Resolve rate
    rate_str = SPEED_RATES.get(speed.lower(), speed if "%" in speed else "-15%")

    # Construct cadence text
    if clean_context and clean_context.lower() != clean_word.lower():
        speech_text = f"{clean_word}. ... {clean_context} ... {clean_word}."
    else:
        speech_text = f"{clean_word}."

    # Cache check
    cache_dir = get_audio_cache_dir()
    cache_key = generate_cache_key(clean_word, clean_context, speed, selected_voice)
    mp3_path = cache_dir / f"{cache_key}.mp3"

    if mp3_path.exists() and mp3_path.stat().st_size > 0:
        return str(mp3_path)

    # Synthesize via edge_tts
    try:
        asyncio.run(_synthesize_edge_tts(speech_text, selected_voice, rate_str, str(mp3_path)))
        return str(mp3_path)
    except Exception as e:
        print(f"Notice: edge-tts synthesis failed with {e}")
        # Clean up incomplete file if any
        if mp3_path.exists() and mp3_path.stat().st_size == 0:
            mp3_path.unlink(missing_ok=True)
        raise e

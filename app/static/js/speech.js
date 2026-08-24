/**
 * Advanced Hybrid Speech Dictation Engine
 * 1. Primary: High-Fidelity Server Neural TTS (Microsoft Azure Neural voices via /api/audio/speak)
 * 2. Fallback: Browser Web Speech API (Only when offline or server unavailable)
 */
class DictationAudio {
  constructor() {
      this.audioElement = new Audio();
    this.synth = window.speechSynthesis || null;
    this.fallbackVoice = null;
    this.isSpeaking = false;
      this.unlocked = false;
      this.pendingPlayback = null;
    
    // User preferences from localStorage
      this.speed = localStorage.getItem('dictation_speed') || 'relaxed';
      this.voice = localStorage.getItem('dictation_voice') || 'aria';
      this.engine = localStorage.getItem('dictation_engine') || 'neural';

    this.initFallbackVoice();
    if (this.synth && this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = () => this.initFallbackVoice();
    }

      // Audio Unlocking & Safari Auto-Recovery on First Touch
      this.initAudioUnlock();
  }

    initAudioUnlock() {
        const unlockHandler = () => {
            this.unlocked = true;

            // If Safari paused initial autoplay on page open, immediately trigger it on first touch!
            if (this.pendingPlayback) {
                const pending = this.pendingPlayback;
                this.pendingPlayback = null;
                this.speak(pending.word, pending.context, pending.onStart, pending.onEnd);
            }

            window.removeEventListener('pointerdown', unlockHandler);
            window.removeEventListener('touchstart', unlockHandler);
            window.removeEventListener('mousedown', unlockHandler);
            window.removeEventListener('click', unlockHandler);
            window.removeEventListener('keydown', unlockHandler);
        };

        window.addEventListener('pointerdown', unlockHandler, {passive: true});
        window.addEventListener('touchstart', unlockHandler, {passive: true});
        window.addEventListener('mousedown', unlockHandler, {passive: true});
        window.addEventListener('click', unlockHandler, {passive: true});
        window.addEventListener('keydown', unlockHandler, {passive: true});
  }

  setSpeed(newSpeed) {
    this.speed = newSpeed || 'relaxed';
    localStorage.setItem('dictation_speed', this.speed);
  }

  setVoice(newVoice) {
    this.voice = newVoice || 'ana';
    localStorage.setItem('dictation_voice', this.voice);
  }

  setEngine(newEngine) {
    this.engine = newEngine || 'neural';
    localStorage.setItem('dictation_engine', this.engine);
  }

  initFallbackVoice() {
    if (!this.synth) return;
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return;

    const preferred = [
      v => v.lang === 'en-US' && v.name.includes('Google'),
      v => v.lang === 'en-US' && v.name.includes('Natural'),
      v => v.lang === 'en-US' && v.name.includes('Samantha'),
      v => v.lang === 'en-US' && v.name.includes('Ava'),
      v => v.lang === 'en-US',
      v => v.lang.startsWith('en')
    ];

    for (const matcher of preferred) {
      const match = voices.find(matcher);
      if (match) {
        this.fallbackVoice = match;
        break;
      }
    }
  }

  /**
   * Main Speak Method
   */
  speak(word, contextSentence = '', onStart = null, onEnd = null) {
    this.stop();

    const cleanWord = (word || '').trim();
    const cleanContext = (contextSentence || '').trim();

    if (!cleanWord) {
      if (onEnd) onEnd();
      return;
    }

    // If user explicitly configured browser speech engine
    if (this.engine === 'browser') {
      this.speakWebSpeech(cleanWord, cleanContext, onStart, onEnd);
      return;
    }

      // 1. High-Quality Server Neural Audio (Azure Neural)
    const params = new URLSearchParams({
      word: cleanWord,
      context: cleanContext,
      speed: this.speed,
      voice: this.voice
    });

    const audioUrl = `/api/audio/speak?${params.toString()}`;
      const audio = this.audioElement || new Audio();
    this.audioElement = audio;

    let fallbackTriggered = false;
      const triggerFallback = (reason) => {
      if (fallbackTriggered) return;
      fallbackTriggered = true;
          console.warn("Neural audio failed (" + reason + "), trying Web Speech fallback...");
      this.speakWebSpeech(cleanWord, cleanContext, onStart, onEnd);
    };

    audio.onplay = () => {
      this.isSpeaking = true;
      if (onStart) onStart();
    };

    audio.onended = () => {
      this.isSpeaking = false;
      if (onEnd) onEnd();
    };

      audio.onerror = (e) => {
          console.warn("Audio loading error for URL:", audioUrl, e);
          triggerFallback('network_error');
    };

    audio.src = audioUrl;

    const playPromise = audio.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            this.unlocked = true;
            this.pendingPlayback = null;
        }).catch((err) => {
            // NotAllowedError is Safari/iOS Autoplay policy
            if (err.name === 'NotAllowedError') {
                console.log("Autoplay paused by Safari. Queued to play on first user touch/tap.");
                this.pendingPlayback = {word: cleanWord, context: cleanContext, onStart, onEnd};
                if (onEnd) onEnd();
            } else {
                console.warn("Audio playback error:", err);
                triggerFallback(err.name);
            }
      });
    }
  }

  /**
   * Browser Web Speech API Fallback (Only used when explicit or server unreachable)
   */
  speakWebSpeech(cleanWord, cleanContext, onStart = null, onEnd = null) {
    if (!this.synth) {
      if (onEnd) onEnd();
      return;
    }

    let speechText = '';
    if (cleanContext && cleanContext.toLowerCase() !== cleanWord.toLowerCase()) {
      speechText = `${cleanWord}. ... ${cleanContext} ... ${cleanWord}.`;
    } else {
      speechText = `${cleanWord}.`;
    }

    const utterance = new SpeechSynthesisUtterance(speechText);
    if (this.fallbackVoice) {
      utterance.voice = this.fallbackVoice;
    }
    utterance.lang = 'en-US';

    const rateMap = {
      'slow': 0.70,
      'relaxed': 0.80,
      'normal': 0.90,
      'fast': 1.05
    };
    utterance.rate = rateMap[this.speed] || 0.80;
    utterance.pitch = 1.0;

    utterance.onstart = () => {
      this.isSpeaking = true;
      if (onStart) onStart();
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      if (onEnd) onEnd();
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      if (onEnd) onEnd();
    };

    this.synth.speak(utterance);
  }

  stop() {
    if (this.audioElement) {
        try {
            this.audioElement.pause();
        } catch (e) {
        }
        this.audioElement.onplay = null;
        this.audioElement.onended = null;
        this.audioElement.onerror = null;
    }
    if (this.synth && this.synth.speaking) {
      this.synth.cancel();
    }
    this.isSpeaking = false;
  }
}

// Global instance
window.dictationAudio = new DictationAudio();

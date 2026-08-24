/**
 * Advanced Hybrid Speech Dictation Engine
 * 1. Primary: High-Fidelity Server Neural TTS (Microsoft Azure Neural voices via /api/audio/speak)
 * 2. Fallback: Browser Web Speech API (American English)
 */
class DictationAudio {
    constructor() {
        this.audioElement = null;
        this.synth = window.speechSynthesis || null;
        this.fallbackVoice = null;
        this.isSpeaking = false;

        // User preferences from localStorage
        this.speed = localStorage.getItem('dictation_speed') || 'relaxed'; // 'slow', 'relaxed', 'normal', 'fast'
        this.voice = localStorage.getItem('dictation_voice') || 'ana'; // 'ana', 'jenny', 'guy'

        this.initFallbackVoice();
        if (this.synth && this.synth.onvoiceschanged !== undefined) {
            this.synth.onvoiceschanged = () => this.initFallbackVoice();
        }
    }

    setSpeed(newSpeed) {
        this.speed = newSpeed || 'relaxed';
        localStorage.setItem('dictation_speed', this.speed);
    }

    setVoice(newVoice) {
        this.voice = newVoice || 'ana';
        localStorage.setItem('dictation_voice', this.voice);
    }

    initFallbackVoice() {
        if (!this.synth) return;
        const voices = this.synth.getVoices();
        if (!voices || voices.length === 0) return;

        const preferred = [
            v => v.lang === 'en-US' && v.name.includes('Google'),
            v => v.lang === 'en-US' && v.name.includes('Natural'),
            v => v.lang === 'en-US' && v.name.includes('Samantha'),
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
     * First tries Neural Server Audio, gracefully falls back to Web Speech API on error.
     */
    speak(word, contextSentence = '', onStart = null, onEnd = null) {
        this.stop();

        const cleanWord = (word || '').trim();
        const cleanContext = (contextSentence || '').trim();

        if (!cleanWord) {
            if (onEnd) onEnd();
            return;
        }

        // 1. Try High-Quality Server Neural Audio
        const params = new URLSearchParams({
            word: cleanWord,
            context: cleanContext,
            speed: this.speed,
            voice: this.voice
        });

        const audioUrl = `/api/audio/speak?${params.toString()}`;
        const audio = new Audio(audioUrl);
        this.audioElement = audio;

        let hasStarted = false;

        audio.onplay = () => {
            hasStarted = true;
            this.isSpeaking = true;
            if (onStart) onStart();
        };

        audio.onended = () => {
            this.isSpeaking = false;
            this.audioElement = null;
            if (onEnd) onEnd();
        };

        audio.onerror = (e) => {
            console.warn("Neural audio streaming unavailable, using browser Web Speech API fallback...", e);
            this.speakWebSpeech(cleanWord, cleanContext, onStart, onEnd);
        };

        // Begin playback
        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.catch((err) => {
                console.warn("Audio play rejected (possible autoplay restriction), trying fallback:", err);
                this.speakWebSpeech(cleanWord, cleanContext, onStart, onEnd);
            });
        }
    }

    /**
     * Browser Web Speech API Fallback
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

        // Map speed to rate
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
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
            this.audioElement = null;
        }
        if (this.synth && this.synth.speaking) {
            this.synth.cancel();
        }
        this.isSpeaking = false;
    }
}

// Global instance
window.dictationAudio = new DictationAudio();

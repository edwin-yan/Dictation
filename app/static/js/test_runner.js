/**
 * Interactive Spelling Test Runner
 * Manages test progression, audio prompts, answer capture, and backend submission.
 */

document.addEventListener('DOMContentLoaded', () => {
    const config = window.TEST_CONFIG;
    if (!config || !config.words || config.words.length === 0) {
        console.error("Test configuration or words missing.");
        return;
    }

    const words = config.words;
    let currentIndex = 0;
    const recordedAnswers = [];
    let isSubmitting = false;
    let lastSubmissionAttempt = 0;

    // DOM Elements with fallback selectors
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    const audioBtn = document.getElementById('audio-speaker-btn') || document.getElementById('btn-play-audio');
    const wordInput = document.getElementById('spelling-input');
    const inputWarningHint = document.getElementById('input-warning-hint');
    const nextBtn = document.getElementById('next-btn') || document.getElementById('btn-submit-word');
    const testForm = document.getElementById('test-form');
    const testStage = document.getElementById('test-stage') || document.getElementById('test-view');
    const loadingStage = document.getElementById('loading-stage') || document.getElementById('submitting-overlay');

    function getMinRequiredLength() {
        const currentWord = words[currentIndex];
        if (!currentWord || !currentWord.word) return 2;
        const cleanWord = currentWord.word.trim();
        return Math.min(2, cleanWord.length);
    }

    function showInputWarning() {
        const minLength = getMinRequiredLength();
        if (wordInput) {
            wordInput.classList.remove('input-shake');
            void wordInput.offsetWidth; // Force DOM reflow to re-trigger animation
            wordInput.classList.add('input-shake');
            wordInput.focus();
        }
        if (inputWarningHint) {
            inputWarningHint.innerText = minLength === 1
                ? 'Please type at least 1 character before moving to the next word!'
                : 'Please type at least 2 characters before moving to the next word!';
            inputWarningHint.style.display = 'block';
        }
    }

    function updateProgress() {
        const currentNum = currentIndex + 1;
        const total = words.length;
        const pct = Math.round((currentIndex / total) * 100);

        if (progressFill) progressFill.style.width = `${pct}%`;
        if (progressText) progressText.innerText = `Word ${currentNum} of ${total}`;
        if (progressPercentage) progressPercentage.innerText = `${pct}% Complete`;
    }

    function playCurrentWord() {
        const currentWord = words[currentIndex];
        if (!currentWord || !window.dictationAudio) return;

        if (audioBtn) audioBtn.classList.add('speaking');

        window.dictationAudio.speak(
            currentWord.word,
            currentWord.context_sentence,
            () => {
                if (audioBtn) audioBtn.classList.add('speaking');
            },
            () => {
                if (audioBtn) audioBtn.classList.remove('speaking');
            }
        );
    }

    function loadWord(index) {
        if (index >= words.length) {
            finishTest();
            return;
        }

        isSubmitting = false;
        currentIndex = index;
        updateProgress();

        if (inputWarningHint) {
            inputWarningHint.style.display = 'none';
        }

        if (wordInput) {
            wordInput.value = '';
            wordInput.classList.remove('input-shake');
            wordInput.disabled = false;
            wordInput.focus();
        }

        if (nextBtn) {
            nextBtn.innerText = (currentIndex === words.length - 1) ? 'Finish Quest 🎉' : 'Next Word ➔';
            nextBtn.disabled = false;
            nextBtn.style.opacity = '0.75';
        }

        // Play word audio with small delay
        setTimeout(() => {
            playCurrentWord();
        }, 250);
    }

    function handleWordSubmission() {
        const now = Date.now();
        if (now - lastSubmissionAttempt < 150) return;
        lastSubmissionAttempt = now;

        if (isSubmitting) return;
        if (currentIndex >= words.length) return;

        const currentWord = words[currentIndex];
        const studentInput = wordInput ? wordInput.value.trim() : '';
        const minLength = getMinRequiredLength();

        if (studentInput.length < minLength) {
            showInputWarning();
            return;
        }

        isSubmitting = true;

        if (inputWarningHint) inputWarningHint.style.display = 'none';
        if (wordInput) wordInput.classList.remove('input-shake');

        // Record answer
        recordedAnswers[currentIndex] = {
            word: currentWord.word,
            context_sentence: currentWord.context_sentence || '',
            student_input: studentInput
        };

        // Advance to next word
        if (currentIndex + 1 < words.length) {
            loadWord(currentIndex + 1);
        } else {
            finishTest();
        }
    }

    async function finishTest() {
        // Show loading stage
        if (testStage) testStage.style.display = 'none';
        if (loadingStage) loadingStage.style.display = 'block';
        if (progressFill) progressFill.style.width = '100%';
        if (progressPercentage) progressPercentage.innerText = '100% Complete';

        const payload = {
            student_id: config.student_id,
            list_id: config.list_id,
            test_type: config.test_type,
            title: config.title,
            answers: recordedAnswers
        };

        try {
            const response = await fetch('/api/test/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();
            if (data.success && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.error || 'There was an error saving your quest results.');
                if (testStage) testStage.style.display = 'block';
                if (loadingStage) loadingStage.style.display = 'none';
            }
        } catch (err) {
            console.error('Submission error:', err);
            alert('Unable to submit quest results. Please check your network connection.');
            if (testStage) testStage.style.display = 'block';
            if (loadingStage) loadingStage.style.display = 'none';
        }
    }

    // Event Listeners
    if (audioBtn) {
        audioBtn.addEventListener('click', (e) => {
            e.preventDefault();
            playCurrentWord();
            if (wordInput) wordInput.focus();
        });
    }

    if (testForm) {
        testForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleWordSubmission();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', (e) => {
            e.preventDefault();
            handleWordSubmission();
        });
    }

    if (wordInput) {
        wordInput.addEventListener('input', () => {
            const minLength = getMinRequiredLength();
            const currentVal = wordInput.value.trim();
            if (currentVal.length >= minLength) {
                if (inputWarningHint) inputWarningHint.style.display = 'none';
                wordInput.classList.remove('input-shake');
                if (nextBtn) nextBtn.style.opacity = '1';
            } else {
                if (nextBtn) nextBtn.style.opacity = '0.75';
            }
        });

        wordInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleWordSubmission();
            }
        });
    }

    // Keyboard shortcut: Ctrl + Space or Cmd + Space or Alt + R for repeat audio
    document.addEventListener('keydown', (e) => {
        if (((e.ctrlKey || e.metaKey) && e.code === 'Space') || (e.altKey && e.code === 'KeyR')) {
            e.preventDefault();
            playCurrentWord();
        }
    });

    // Start first word
    loadWord(0);
});

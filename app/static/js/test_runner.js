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

    // DOM Elements
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const progressPercentage = document.getElementById('progress-percentage');
    const audioBtn = document.getElementById('audio-speaker-btn');
    const wordInput = document.getElementById('spelling-input');
    const nextBtn = document.getElementById('next-btn');
    const testForm = document.getElementById('test-form');
    const testStage = document.getElementById('test-stage');
    const loadingStage = document.getElementById('loading-stage');

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
        if (!currentWord) return;

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

        currentIndex = index;
        updateProgress();

        if (wordInput) {
            wordInput.value = '';
            wordInput.disabled = false;
            wordInput.focus();
        }

        if (nextBtn) {
            nextBtn.innerText = (currentIndex === words.length - 1) ? 'Finish Test 🎉' : 'Next Word ➜';
            nextBtn.disabled = false;
        }

        // Play word with short delay for smooth DOM render
        setTimeout(() => {
            playCurrentWord();
        }, 250);
    }

    function handleWordSubmission() {
        if (currentIndex >= words.length) return;

        const currentWord = words[currentIndex];
        const studentInput = wordInput ? wordInput.value.trim() : '';

        // Record answer
        recordedAnswers[currentIndex] = {
            word: currentWord.word,
            context_sentence: currentWord.context_sentence || '',
            student_input: studentInput
        };

        // Advance to next word without displaying feedback
        if (currentIndex + 1 < words.length) {
            loadWord(currentIndex + 1);
        } else {
            finishTest();
        }
    }

    async function finishTest() {
        // Show loading stage
        if (testStage) testStage.style.display = 'none';
        if (loadingStage) loadingStage.style.display = 'flex';
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
                alert(data.error || 'There was an error saving your test results.');
                if (testStage) testStage.style.display = 'flex';
                if (loadingStage) loadingStage.style.display = 'none';
            }
        } catch (err) {
            console.error('Submission error:', err);
            alert('Unable to submit test results. Please check your network connection.');
            if (testStage) testStage.style.display = 'flex';
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

    // Keyboard shortcut: Ctrl + Space or Alt + R for repeat audio
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey && e.code === 'Space') || (e.altKey && e.code === 'KeyR')) {
            e.preventDefault();
            playCurrentWord();
        }
    });

    // Start first word
    loadWord(0);
});

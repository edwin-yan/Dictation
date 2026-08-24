/**
 * Main application UI helpers
 */

document.addEventListener('DOMContentLoaded', () => {
    // Pre-unlock Audio for Safari / iOS when clicking Quest or Study links
    document.querySelectorAll('a[href*="/challenge/"], a[href*="/study/"]').forEach(link => {
        link.addEventListener('click', () => {
            if (window.dictationAudio && window.dictationAudio.audioElement) {
                try {
                    window.dictationAudio.audioElement.load();
                } catch (e) {
                }
            }
        });
    });

    // Student Switcher in Navbar
    const studentSelect = document.getElementById('navbar-student-select');
    if (studentSelect) {
        studentSelect.addEventListener('change', () => {
            const selectedId = studentSelect.value;
            if (selectedId) {
                window.location.href = `/dashboard?student_id=${selectedId}`;
            }
        });
    }

    // Audio Play Buttons on Results & Dashboard Pages
    document.querySelectorAll('.word-audio-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const word = btn.getAttribute('data-word');
            const context = btn.getAttribute('data-context') || '';

            btn.style.transform = 'scale(1.2)';
            setTimeout(() => {
                btn.style.transform = '';
            }, 200);

            if (window.dictationAudio) {
                window.dictationAudio.speak(word, context);
            }
        });
    });

    // Modal open/close helpers
    document.querySelectorAll('[data-modal-open]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const targetModalId = trigger.getAttribute('data-modal-open');
            const modal = document.getElementById(targetModalId);
            if (modal) modal.classList.add('active');
        });
    });

    document.querySelectorAll('[data-modal-close]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = trigger.closest('.modal-overlay');
            if (modal) modal.classList.remove('active');
        });
    });

    // Close modal when clicking on overlay background
    document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

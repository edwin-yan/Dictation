/**
 * Admin Panel Interactive Helpers
 */

document.addEventListener('DOMContentLoaded', () => {
    // Edit Student Modal Populate
    document.querySelectorAll('.btn-edit-student').forEach(btn => {
        btn.addEventListener('click', () => {
            const studentId = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name');
            const grade = btn.getAttribute('data-grade');
            const avatar = btn.getAttribute('data-avatar');

            const modal = document.getElementById('edit-student-modal');
            const form = document.getElementById('edit-student-form');

            if (modal && form) {
                form.action = `/admin/students/${studentId}/edit`;
                form.querySelector('[name="name"]').value = name;
                form.querySelector('[name="grade"]').value = grade;
                form.querySelector('[name="avatar"]').value = avatar;
                modal.classList.add('active');
            }
        });
    });

    // Edit Word List Modal Populate
    document.querySelectorAll('.btn-edit-list').forEach(btn => {
        btn.addEventListener('click', () => {
            const listId = btn.getAttribute('data-id');
            const title = btn.getAttribute('data-title');
            const description = btn.getAttribute('data-description');
            const category = btn.getAttribute('data-category');

            const modal = document.getElementById('edit-list-modal');
            const form = document.getElementById('edit-list-form');

            if (modal && form) {
                form.action = `/admin/lists/${listId}/edit`;
                form.querySelector('[name="title"]').value = title;
                form.querySelector('[name="description"]').value = description;
                form.querySelector('[name="category"]').value = category;
                modal.classList.add('active');
            }
        });
    });

    // Edit Word Modal Populate
    document.querySelectorAll('.btn-edit-word').forEach(btn => {
        btn.addEventListener('click', () => {
            const wordId = btn.getAttribute('data-id');
            const word = btn.getAttribute('data-word');
            const context = btn.getAttribute('data-context');

            const modal = document.getElementById('edit-word-modal');
            const form = document.getElementById('edit-word-form');

            if (modal && form) {
                form.action = `/admin/words/${wordId}/edit`;
                form.querySelector('[name="word"]').value = word;
                form.querySelector('[name="context_sentence"]').value = context;
                modal.classList.add('active');
            }
        });
    });

    // Matrix Assignment Select All / Deselect All Column or Row
    document.querySelectorAll('.select-all-col').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const listId = btn.getAttribute('data-list-id');
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][name$="_${listId}"]`);
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            checkboxes.forEach(c => c.checked = !allChecked);
        });
    });

    document.querySelectorAll('.select-all-row').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const studentId = btn.getAttribute('data-student-id');
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][name^="assign_${studentId}_"]`);
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            checkboxes.forEach(c => c.checked = !allChecked);
        });
    });
});

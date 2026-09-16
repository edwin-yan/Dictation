/**
 * Admin Panel Interactive Helpers
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Edit Student Modal Populate
    document.querySelectorAll('.btn-edit-student').forEach(btn => {
        btn.addEventListener('click', () => {
            const studentId = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name') || '';
            const avatar = btn.getAttribute('data-avatar') || '🦊';
            const folderIds = JSON.parse(btn.getAttribute('data-folders') || '[]');

            const modal = document.getElementById('edit-student-modal');
            const form = document.getElementById('edit-student-form');

            if (modal && form) {
                form.action = `/admin/students/${studentId}/edit`;

                const nameInput = form.querySelector('[name="name"]');
                if (nameInput) nameInput.value = name;

                const avatarSelect = form.querySelector('[name="avatar"]');
                if (avatarSelect) avatarSelect.value = avatar;

                // Set folder checkboxes
                form.querySelectorAll('.edit-folder-checkbox').forEach(cb => {
                    cb.checked = folderIds.includes(parseInt(cb.value));
                });

                modal.classList.add('active');
            }
        });
    });

    // 2. Edit Word List Modal Populate
    document.querySelectorAll('.btn-edit-list').forEach(btn => {
        btn.addEventListener('click', () => {
            const listId = btn.getAttribute('data-id');
            const title = btn.getAttribute('data-title') || '';
            const description = btn.getAttribute('data-description') || '';
            const folderId = btn.getAttribute('data-folder-id') || '';

            const modal = document.getElementById('edit-list-modal');
            const form = document.getElementById('edit-list-form');

            if (modal && form) {
                form.action = `/admin/lists/${listId}/edit`;

                const titleInput = form.querySelector('[name="title"]');
                if (titleInput) titleInput.value = title;

                const descInput = form.querySelector('[name="description"]');
                if (descInput) descInput.value = description;

                const folderSelect = form.querySelector('[name="folder_id"]');
                if (folderSelect) folderSelect.value = folderId;

                modal.classList.add('active');
            }
        });
    });

    // 3. Edit Folder Modal Populate
    document.querySelectorAll('.btn-edit-folder').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-id');
            const name = btn.getAttribute('data-name') || '';
            const desc = btn.getAttribute('data-desc') || '';
            const icon = btn.getAttribute('data-icon') || '📁';

            const modal = document.getElementById('edit-folder-modal');
            const form = document.getElementById('edit-folder-form');

            if (modal && form) {
                form.action = `/admin/folders/${id}/edit`;

                const nameInput = form.querySelector('[name="name"]');
                if (nameInput) nameInput.value = name;

                const descInput = form.querySelector('[name="description"]');
                if (descInput) descInput.value = desc;

                const iconSelect = form.querySelector('[name="icon"]');
                if (iconSelect) iconSelect.value = icon;

                modal.classList.add('active');
            }
        });
    });

    // 4. Edit Word Modal Populate
    document.querySelectorAll('.btn-edit-word').forEach(btn => {
        btn.addEventListener('click', () => {
            const wordId = btn.getAttribute('data-id');
            const word = btn.getAttribute('data-word') || '';
            const context = btn.getAttribute('data-context') || '';

            const modal = document.getElementById('edit-word-modal');
            const form = document.getElementById('edit-word-form');

            if (modal && form) {
                form.action = `/admin/words/${wordId}/edit`;

                const wordInput = form.querySelector('[name="word"]');
                if (wordInput) wordInput.value = word;

                const contextInput = form.querySelector('[name="context_sentence"]');
                if (contextInput) contextInput.value = context;

                modal.classList.add('active');
            }
        });
    });

    // 5. Matrix Assignment Select All / Deselect All Column or Row
    document.querySelectorAll('.select-all-col').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const folderId = btn.getAttribute('data-folder-id');
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][name$="_${folderId}"]`);
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            checkboxes.forEach(c => c.checked = !allChecked);
        });
    });

    document.querySelectorAll('.select-all-row').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const studentId = btn.getAttribute('data-student-id');
            const checkboxes = document.querySelectorAll(`input[type="checkbox"][name^="assoc_${studentId}_"]`);
            const allChecked = Array.from(checkboxes).every(c => c.checked);
            checkboxes.forEach(c => c.checked = !allChecked);
        });
    });

    // 6. Create List in Target Folder Helper
    document.querySelectorAll('.btn-create-list-in-folder').forEach(btn => {
        btn.addEventListener('click', () => {
            const folderId = btn.getAttribute('data-folder-id');
            const modal = document.getElementById('create-list-modal');
            const select = document.getElementById('create-folder-select');
            if (select && folderId !== null && folderId !== undefined) {
                select.value = folderId;
            }
            if (modal) {
                modal.classList.add('active');
            }
        });
    });

    // 7. Word Lists Collapsible Accordion (Compact by Default)
    const listCards = document.querySelectorAll('.collapsible-list-card');
    const btnToggleAll = document.getElementById('btn-toggle-all-lists');
    const toggleAllIcon = document.getElementById('toggle-all-icon');
    const toggleAllText = document.getElementById('toggle-all-text');

    function collapseCard(card) {
        if (!card) return;
        card.classList.remove('is-expanded');
        const header = card.querySelector('.list-accordion-header');
        if (header) header.setAttribute('aria-expanded', 'false');
    }

    function expandCard(card, updateHash = false) {
        if (!card) return;
        card.classList.add('is-expanded');
        const header = card.querySelector('.list-accordion-header');
        if (header) header.setAttribute('aria-expanded', 'true');
        if (updateHash) {
            const listId = card.getAttribute('data-list-id');
            if (listId && history.replaceState) {
                history.replaceState(null, '', `#list-${listId}`);
            }
        }
    }

    function updateToggleAllButtonState() {
        if (!btnToggleAll) return;
        const total = listCards.length;
        const expandedCount = document.querySelectorAll('.collapsible-list-card.is-expanded').length;
        if (total > 0 && expandedCount === total) {
            if (toggleAllIcon) toggleAllIcon.textContent = '📁';
            if (toggleAllText) toggleAllText.textContent = 'Collapse All';
        } else {
            if (toggleAllIcon) toggleAllIcon.textContent = '📂';
            if (toggleAllText) toggleAllText.textContent = 'Expand All';
        }
    }

    listCards.forEach(card => {
        const header = card.querySelector('.list-accordion-header');
        if (!header) return;

        header.addEventListener('click', (e) => {
            // Prevent toggle if clicking on edit/delete action buttons, inputs, or forms
            if (e.target.closest('[data-no-toggle="true"]') ||
                e.target.closest('button') ||
                e.target.closest('form') ||
                e.target.closest('input')) {
                return;
            }

            const isCurrentlyExpanded = card.classList.contains('is-expanded');

            if (isCurrentlyExpanded) {
                // Clicking an already expanded list collapses it
                collapseCard(card);
                if (history.replaceState) {
                    history.replaceState(null, '', window.location.pathname + window.location.search);
                }
            } else {
                // Accordion behavior: collapse all other lists and expand this one
                listCards.forEach(otherCard => {
                    if (otherCard !== card) {
                        collapseCard(otherCard);
                    }
                });
                expandCard(card, true);
            }
            updateToggleAllButtonState();
        });

        // Keyboard accessibility: Enter or Space on header
        header.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                if (e.target.closest('[data-no-toggle="true"]') ||
                    e.target.closest('button') ||
                    e.target.closest('form')) return;
                e.preventDefault();
                header.click();
            }
        });
    });

    // Expand All / Collapse All Toggle Button
    if (btnToggleAll) {
        btnToggleAll.addEventListener('click', () => {
            const total = listCards.length;
            const expandedCount = document.querySelectorAll('.collapsible-list-card.is-expanded').length;
            const shouldExpandAll = expandedCount < total;

            listCards.forEach(card => {
                if (shouldExpandAll) {
                    expandCard(card, false);
                } else {
                    collapseCard(card);
                }
            });

            if (!shouldExpandAll && history.replaceState) {
                history.replaceState(null, '', window.location.pathname + window.location.search);
            }
            updateToggleAllButtonState();
        });
    }

    // Auto-expand list matching URL hash (after adding/editing/deleting a word, or opening a direct link)
    if (window.location.hash) {
        const hash = window.location.hash.replace('#', '');
        let targetCard = null;
        if (hash.startsWith('list-card-')) {
            targetCard = document.getElementById(hash);
        } else if (hash.startsWith('list-')) {
            const id = hash.replace('list-', '');
            targetCard = document.getElementById(`list-card-${id}`);
        }
        if (targetCard) {
            expandCard(targetCard, false);
            updateToggleAllButtonState();
            setTimeout(() => {
                targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 150);
        }
    }
});

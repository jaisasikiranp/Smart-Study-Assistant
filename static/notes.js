document.addEventListener('DOMContentLoaded', () => {
    // Basic search interactivity
    const searchBox = document.getElementById('noteSearch');
    if (searchBox) {
        searchBox.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const cards = document.querySelectorAll('.note-card');
            cards.forEach(card => {
                const title = card.querySelector('h3').textContent.toLowerCase();
                const content = card.querySelector('p').textContent.toLowerCase();
                if (title.includes(query) || content.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Modal Control
    const openModalBtn = document.getElementById('addNoteBtn');
    const modal = document.getElementById('addNoteModal');
    const closeModalBtn = document.getElementById('closeModal');

    if (openModalBtn && modal) {
        openModalBtn.addEventListener('click', () => modal.style.display = 'flex');
    }

    if (closeModalBtn && modal) {
        closeModalBtn.addEventListener('click', () => modal.style.display = 'none');
    }

    // Close modal on click outside content
    window.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
});

// ================================
// Qubit Learn - Global JS
// Handles: Forms, Flashcards, Theme Toggle
// ================================

document.addEventListener('DOMContentLoaded', function() {
    /* ------------------------------
       THEME TOGGLE (Light / Dark)
    ------------------------------ */
    const toggleBtn = document.getElementById('themeToggle');
    const body = document.body;

    // Load saved theme from localStorage
    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-theme');
        if (toggleBtn) toggleBtn.textContent = '☀️';
    } else {
        if (toggleBtn) toggleBtn.textContent = '🌙';
    }

    // Handle toggle click
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('dark-theme');

            if (body.classList.contains('dark-theme')) {
                toggleBtn.textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            } else {
                toggleBtn.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            }
        });
    }

    /* ------------------------------
       DONATE FORM HANDLER
    ------------------------------ */
    const donateForm = document.getElementById('donateForm');
    if (donateForm) {
        donateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // TODO: Replace with real donation logic
            alert('Thank you for your donation! (Implement backend integration)');
        });
    }

    /* ------------------------------
       UPLOAD FORM HANDLER
    ------------------------------ */
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // TODO: Replace with real upload logic
            alert('File uploaded! (Implement backend integration)');
        });
    }

    /* ------------------------------
       FLASHCARDS (Dynamic Loading)
    ------------------------------ */
    const flashcardContainer = document.getElementById('flashcardContainer');
    if (flashcardContainer) {
        // TODO: Replace with real API call to fetch flashcards
        const sampleFlashcards = [
            { question: 'What is a qubit?', answer: 'A qubit is the basic unit of quantum information.' },
            { question: 'What is superposition?', answer: 'Superposition is a fundamental principle of quantum mechanics.' },
        ];
        sampleFlashcards.forEach(card => {
            const div = document.createElement('div');
            div.className = 'flashcard';
            div.innerHTML = `<strong>Q:</strong> ${card.question}<br><strong>A:</strong> ${card.answer}`;
            flashcardContainer.appendChild(div);
        });
    }
});

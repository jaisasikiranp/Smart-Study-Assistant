document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Remove active from all
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active to current
            link.classList.add('active');
            
            // Debugging log for the user
            const pageName = link.textContent.trim();
            console.log(`[NAV DEBUG] Clicked on: ${pageName}`);
            
            if (pageName.includes('Courses')) {
                console.log("[NAV DEBUG] Courses link targeted - applying high-contrast highlight.");
            }
        });
    });
});

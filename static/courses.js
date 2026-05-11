document.addEventListener('DOMContentLoaded', () => {
    let courses = [];
    const courseGrid = document.getElementById('courseGrid');
    const searchBar = document.getElementById('searchBar');
    const addCourseForm = document.getElementById('addCourseForm');
    const courseDetailModal = document.getElementById('courseDetailModal');
    const addCourseModal = document.getElementById('addCourseModal');
    const pdfForm = document.getElementById('pdfUploadForm');
    let currentCourseId = null;

    // 1. FETCH ALL COURSES
    const fetchCourses = async () => {
        try {
            const res = await fetch('/courses');
            courses = await res.json();
            renderCourses(courses);
        } catch (err) {
            console.error("Error fetching courses:", err);
        }
    };

    // 2. RENDER COURSES (Screenshot 1 Style)
    const renderCourses = (filteredCourses) => {
        if (filteredCourses.length === 0) {
            courseGrid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 4rem; color: #64748b; background: rgba(0,0,0,0.02); border-radius: 1rem;">
                    <p>No courses found. Start by adding your first one!</p>
                </div>`;
            return;
        }
        courseGrid.innerHTML = filteredCourses.map(c => `
            <div class="course-card" onclick="openDetails(${c.id})" style="border-left: 4px solid #6366f1; padding: 1.75rem; background: white; border-radius: 1rem; box-shadow: 0 4px 15px rgba(0,0,0,0.04); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; height: 100%;">
                <h3 style="color: #1e293b; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem; font-size: 1.1rem; letter-spacing: 0.02em;">${c.title}</h3>
                <p style="color: #64748b; font-size: 0.875rem; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${c.description || 'No description provided.'}</p>
            </div>
        `).join('');
    };

    // 3. SEARCH LOGIC
    searchBar.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        const filtered = courses.filter(c => 
            c.title.toLowerCase().includes(query) || 
            c.description.toLowerCase().includes(query)
        );
        renderCourses(filtered);
    });

    // 4. ADD COURSE LOGIC (Screenshot 3)
    addCourseForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const title = document.getElementById('courseTitle').value;
        const description = document.getElementById('courseDesc').value;

        try {
            const res = await fetch('/add_course', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, description })
            });

            if (res.ok) {
                const newCourse = await res.json();
                courses.unshift(newCourse);
                renderCourses(courses);
                closeAddCourseModal();
                addCourseForm.reset();
            }
        } catch (err) {
            console.error("Add Course Error:", err);
        }
    });

    // 5. COURSE DETAIL LOGIC (Screenshot 2)
    window.openDetails = async (id) => {
        currentCourseId = id;
        try {
            const res = await fetch(`/courses/${id}`);
            const data = await res.json();

            document.getElementById('detailTitle').innerText = data.title;
            document.getElementById('detailDesc').innerText = data.description;
            
            const pdfList = document.getElementById('pdfList');
            if (!data.pdfs || data.pdfs.length === 0) {
                pdfList.innerHTML = `
                    <div style="text-align: center; padding: 3rem; color: #94a3b8; border: 2px dashed #f1f5f9; border-radius: 1rem; width: 100%;">
                        <p>No study materials uploaded yet.</p>
                    </div>`;
            } else {
                pdfList.innerHTML = data.pdfs.map(p => `
                    <li style="display: flex; justify-content: space-between; align-items: center; padding: 1.25rem; background: white; border: 1px solid #f1f5f9; border-radius: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
                        <div style="display: flex; align-items: center; gap: 1rem;">
                            <span style="font-size: 1.5rem; color: #ef4444;">📕</span>
                            <span style="font-weight: 500; color: #334155; font-size: 1rem;">${p.filename}</span>
                        </div>
                        <div style="display: flex; gap: 0.75rem;">
                            <a href="${p.filepath}" target="_blank" style="padding: 0.5rem 1.25rem; background: #6366f1; color: white; border-radius: 0.5rem; text-decoration: none; font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem;">View</a>
                            <a href="${p.filepath}" download style="padding: 0.5rem 1.25rem; background: #10b981; color: white; border-radius: 0.5rem; text-decoration: none; font-weight: 600; font-size: 0.85rem; display: flex; align-items: center; gap: 0.4rem;">Download</a>
                        </div>
                    </li>
                `).join('');
            }
            courseDetailModal.style.display = 'flex';
        } catch (err) {
            console.error("Open Details Error:", err);
        }
    };

    // 6. HELPER FUNCTIONS
    window.openAddCourseModal = () => {
        addCourseModal.style.display = 'flex';
    };

    window.closeAddCourseModal = () => {
        addCourseModal.style.display = 'none';
        addCourseForm.reset();
    };

    window.uploadSelectedFile = () => {
        document.getElementById('pdfUploadBtn').click();
    };

    pdfForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById('pdfFile');
        if (!fileInput.files[0]) return;

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch(`/upload_pdf/${currentCourseId}`, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                openDetails(currentCourseId);
                fileInput.value = '';
            }
        } catch (err) {
            console.error("Upload Error:", err);
        }
    });

    window.closeModal = () => {
        courseDetailModal.style.display = 'none';
    };

    fetchCourses();
});
